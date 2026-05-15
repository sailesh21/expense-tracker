# SplitEasy — Expense Tracker

A group expense splitting app built with FastAPI + PostgreSQL.

## Prerequisites

- Python 3.11+
- PostgreSQL running locally

## Setup

### 1. Create the database

```bash
psql -U postgres -c "CREATE DATABASE spliteasy;"
psql -U postgres -c "CREATE USER aira WITH PASSWORD 'password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE spliteasy TO aira;"
```

> If your local PostgreSQL user is different, update `DATABASE_URL` in [main.py](main.py) or set the environment variable (see step 3).

### 2. Create and activate the virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Environment variables

All variables are optional — defaults work for local development.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://aira:password@localhost:5432/spliteasy` | PostgreSQL connection string |
| `ADMIN_USER` | `admin` | Username for category admin access |
| `ADMIN_PASS` | `changeme` | Password for category admin access |

Set them before starting the server:

```bash
export DATABASE_URL="postgresql://<user>:<password>@localhost:5432/<dbname>"
export ADMIN_USER="yourname"
export ADMIN_PASS="yourpassword"
```

## Starting the server

```bash
.venv/bin/uvicorn main:app --port 8000
```

Or if the virtual environment is already activated:

```bash
uvicorn main:app --port 8000
```

The app will be available at **http://localhost:8000**.  
Database tables and default categories are created automatically on first startup.

For auto-reload during development:

```bash
uvicorn main:app --port 8000 --reload
```

## Stopping the server

Press `Ctrl + C` in the terminal where the server is running.

If the server is running in the background and you need to stop it by port:

```bash
lsof -ti :8000 | xargs kill
```

## Features

### Dashboard
- **Total Spent** — sum of all expenses
- **My Share** — your personal portion across all expenses you're part of
- **You Owe / You're Owed** — your net balance
- **Identity switcher** — click your name in the top-right header to switch which person is "You"

### People
- Add members by name (names are unique, case-insensitive)
- Mark one person as **You** to track your personal balances — also switchable directly from the header

### Expenses
- Add, edit, and delete expenses with description, amount, category, payer, split, and date
- Split each expense between any subset of people
- Edit correctly restores the original split selection

### Balances & Settle Up
- Net balance view per person
- Suggested minimum payments to settle all debts
- Record a settlement directly from the Settle Up tab

### Categories (admin-protected)
Categories are stored in the database. The five defaults (Food, Travel, Shopping, Bills, Other) are seeded on first startup.

To add or remove categories, log in as admin from the **People → Categories** card:
1. Click **🔒 Admin**
2. Enter the admin username and password
3. Add a category with an emoji icon and name, or remove existing ones with ✕

Admin access is session-only (stored in memory, cleared on page refresh).

## Project structure

```
expense-tracker/
├── index.html       # Frontend (served by FastAPI)
├── main.py          # FastAPI app + API routes
├── schema.sql       # Database schema (auto-applied on startup)
├── requirements.txt # Python dependencies
└── .venv/           # Virtual environment
```

## API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/people` | — | List all people |
| POST | `/api/people` | — | Add a person |
| PATCH | `/api/people/:id` | — | Update a person (set as Me) |
| DELETE | `/api/people/:id` | — | Remove a person |
| GET | `/api/expenses` | — | List all expenses |
| POST | `/api/expenses` | — | Add an expense |
| PUT | `/api/expenses/:id` | — | Update an expense |
| DELETE | `/api/expenses/:id` | — | Delete an expense |
| GET | `/api/categories` | — | List all categories |
| GET | `/api/admin/verify` | Admin | Verify admin credentials |
| POST | `/api/categories` | Admin | Add a category |
| DELETE | `/api/categories/:id` | Admin | Remove a category |
