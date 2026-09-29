CREATE TABLE organizations (
    id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);
CREATE TABLE users (
    id TEXT PRIMARY KEY, login TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('government_analyst','hospital_analyst','platform_admin')),
    hospital_id TEXT REFERENCES organizations(id),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    must_change_password INTEGER NOT NULL DEFAULT 0 CHECK (must_change_password IN (0,1)),
    version INTEGER NOT NULL DEFAULT 1,
    CHECK ((role = 'hospital_analyst' AND hospital_id IS NOT NULL) OR (role <> 'hospital_analyst' AND hospital_id IS NULL))
);
CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
    version INTEGER NOT NULL, created DOUBLE PRECISION NOT NULL,
    last_active DOUBLE PRECISION NOT NULL
);
CREATE INDEX sessions_user ON sessions(user_id);
CREATE TABLE csrf_tokens (
    token_hash TEXT PRIMARY KEY, binding TEXT NOT NULL, expires DOUBLE PRECISION NOT NULL
);
CREATE INDEX csrf_expiration ON csrf_tokens(expires);
CREATE TABLE attempts (
    bucket TEXT PRIMARY KEY, started DOUBLE PRECISION NOT NULL, count INTEGER NOT NULL
);
CREATE TABLE audit_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, at DOUBLE PRECISION NOT NULL,
    actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, result TEXT NOT NULL
);
