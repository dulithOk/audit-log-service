-- Executed once when the Postgres container is first created.
-- Alembic handles schema migrations; this only sets up extensions.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- enables fast LIKE/ILIKE on text columns
