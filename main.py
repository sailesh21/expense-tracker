from contextlib import asynccontextmanager
from datetime import date as date_type
from typing import Optional
import os

import secrets

import asyncpg
from asyncpg import UniqueViolationError
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://aira:password@localhost:5432/spliteasy",
)
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "changeme")

_http_basic = HTTPBasic(auto_error=True)

def require_admin(credentials: HTTPBasicCredentials = Depends(_http_basic)):
    ok = (
        secrets.compare_digest(credentials.username.encode(), ADMIN_USER.encode()) and
        secrets.compare_digest(credentials.password.encode(), ADMIN_PASS.encode())
    )
    if not ok:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )

pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        with open("schema.sql") as f:
            await conn.execute(f.read())
    yield
    await pool.close()


app = FastAPI(title="SplitEasy API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ─────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    id: str
    name: str
    icon: str
    color: str = '#ede9fe'


class PersonCreate(BaseModel):
    id: str
    name: str
    is_me: bool = False


class PersonPatch(BaseModel):
    is_me: Optional[bool] = None


class ExpenseCreate(BaseModel):
    id: str
    description: str
    amount: float
    category: str
    paid_by: str
    split_with: list[str]
    date: str


class ExpenseUpdate(BaseModel):
    description: str
    amount: float
    category: str
    paid_by: str
    split_with: list[str]
    date: str


# ── Categories ─────────────────────────────────────────────────────────────

@app.get("/api/categories")
async def list_categories():
    rows = await pool.fetch(
        "SELECT id, name, icon, color FROM categories ORDER BY created_at"
    )
    return [dict(r) for r in rows]


@app.get("/api/admin/verify")
async def verify_admin(_=Depends(require_admin)):
    return {"ok": True}


@app.post("/api/categories", status_code=201)
async def create_category(body: CategoryCreate, _=Depends(require_admin)):
    try:
        await pool.execute(
            "INSERT INTO categories (id, name, icon, color) VALUES ($1, $2, $3, $4)",
            body.id, body.name, body.icon, body.color,
        )
    except UniqueViolationError:
        raise HTTPException(400, f"Category '{body.name}' already exists.")
    return {"ok": True}


@app.delete("/api/categories/{category_id}", status_code=204)
async def delete_category(category_id: str, _=Depends(require_admin)):
    used = await pool.fetchval(
        "SELECT 1 FROM expenses WHERE category = $1 LIMIT 1", category_id
    )
    if used:
        raise HTTPException(400, "Category is used by existing expenses.")
    await pool.execute("DELETE FROM categories WHERE id = $1", category_id)


# ── People ─────────────────────────────────────────────────────────────────

@app.get("/api/people")
async def list_people():
    rows = await pool.fetch(
        "SELECT id, name, is_me FROM people ORDER BY created_at"
    )
    return [dict(r) for r in rows]


@app.post("/api/people", status_code=201)
async def create_person(body: PersonCreate):
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                if body.is_me:
                    await conn.execute("UPDATE people SET is_me = FALSE")
                await conn.execute(
                    "INSERT INTO people (id, name, is_me) VALUES ($1, $2, $3)",
                    body.id, body.name, body.is_me,
                )
    except UniqueViolationError:
        raise HTTPException(400, f"'{body.name}' is already in the group.")
    return {"ok": True}


@app.patch("/api/people/{person_id}")
async def patch_person(person_id: str, body: PersonPatch):
    async with pool.acquire() as conn:
        async with conn.transaction():
            if body.is_me is True:
                await conn.execute("UPDATE people SET is_me = FALSE")
                await conn.execute(
                    "UPDATE people SET is_me = TRUE WHERE id = $1", person_id
                )
    return {"ok": True}


@app.delete("/api/people/{person_id}", status_code=204)
async def delete_person(person_id: str):
    async with pool.acquire() as conn:
        used = await conn.fetchval(
            "SELECT 1 FROM expenses WHERE paid_by=$1 OR $1=ANY(split_with) LIMIT 1",
            person_id,
        )
        if used:
            raise HTTPException(
                400, "Person is part of existing expenses. Delete those first."
            )
        await conn.execute("DELETE FROM people WHERE id=$1", person_id)


# ── Expenses ───────────────────────────────────────────────────────────────

@app.get("/api/expenses")
async def list_expenses():
    rows = await pool.fetch(
        "SELECT id, description, amount, category, paid_by, split_with, date::text "
        "FROM expenses ORDER BY created_at DESC"
    )
    return [dict(r) for r in rows]


@app.post("/api/expenses", status_code=201)
async def create_expense(body: ExpenseCreate):
    await pool.execute(
        "INSERT INTO expenses (id, description, amount, category, paid_by, split_with, date) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7)",
        body.id, body.description, body.amount, body.category,
        body.paid_by, body.split_with, date_type.fromisoformat(body.date),
    )
    return {"ok": True}


@app.put("/api/expenses/{expense_id}")
async def update_expense(expense_id: str, body: ExpenseUpdate):
    result = await pool.execute(
        "UPDATE expenses SET description=$1, amount=$2, category=$3, "
        "paid_by=$4, split_with=$5, date=$6 WHERE id=$7",
        body.description, body.amount, body.category,
        body.paid_by, body.split_with, date_type.fromisoformat(body.date), expense_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(404, "Expense not found")
    return {"ok": True}


@app.delete("/api/expenses/{expense_id}", status_code=204)
async def delete_expense(expense_id: str):
    await pool.execute("DELETE FROM expenses WHERE id=$1", expense_id)


# ── Serve frontend ─────────────────────────────────────────────────────────
app.mount("/", StaticFiles(directory=".", html=True), name="static")
