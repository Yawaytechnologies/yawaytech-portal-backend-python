# Supabase Migration Plan

This project can be moved to a new Supabase project without changing the Alembic history.

## What to change

Update these values in `.env` for the new Supabase project:

- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_PROFILE_BUCKET`
- `SUPABASE_EVIDENCE_BUCKET`

Database access and storage access are separate:

- `DATABASE_URL` is for PostgreSQL and Alembic migrations.
- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are for Supabase Storage.

## Recommended migration order

1. Create the new Supabase project.
2. Collect the new database password, project URL, and service role key.
3. Create a new local `.env` pointing to the new project.
4. Install dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

5. Run Alembic against the new database:

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\alembic upgrade head
```

6. Verify the schema:

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python simple_check.py
```

7. Create the required storage buckets in the new Supabase project:

- profile bucket: value from `SUPABASE_PROFILE_BUCKET`
- evidence bucket: value from `SUPABASE_EVIDENCE_BUCKET`

8. If you need old data too, migrate the data separately after the schema is created.

## Important notes

- Alembic migration files already define the tables. Running `upgrade head` on an empty new Supabase database is the cleanest path.
- Do not copy the old `alembic_version` row manually into an empty database. Let Alembic create everything.
- If you are also moving application data, use a PostgreSQL dump/restore or table-by-table copy after schema creation.
- For migrations, prefer a PostgreSQL URL using the `postgresql+psycopg://` driver.

## Current repo behavior

- The app normalizes older PostgreSQL URL formats.
- Alembic now normalizes `postgres://` and `postgresql+psycopg2://` to `postgresql+psycopg://` too, so it matches app behavior.
- The sample env file now includes the Supabase and PostgreSQL variables needed for a new project.
