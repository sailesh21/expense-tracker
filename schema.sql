CREATE TABLE IF NOT EXISTS people (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_me BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS people_name_unique ON people (LOWER(name));

CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT '📦',
    color TEXT NOT NULL DEFAULT '#ede9fe',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO categories (id, name, icon, color) VALUES
    ('food',     'Food',     '🍔', '#fef3c7'),
    ('travel',   'Travel',   '✈️', '#dbeafe'),
    ('shopping', 'Shopping', '🛍️', '#fce7f3'),
    ('bills',    'Bills',    '💡', '#d1fae5'),
    ('other',    'Other',    '📦', '#ede9fe')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS expenses (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    category TEXT NOT NULL DEFAULT 'other',
    paid_by TEXT NOT NULL REFERENCES people(id) ON DELETE RESTRICT,
    split_with TEXT[] NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
