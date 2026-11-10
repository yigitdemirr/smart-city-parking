# Web service (Python 3.12 + FastAPI)

Planned for Lab 5 (service and database foundation). Design is fixed in M1:

- API contract: [`../api/openapi.yaml`](../api/openapi.yaml)
- Modules: `auth`, `search`, `reservations`, `payments` (simulated), `operations` (idempotency), `admin`, `jobs/expiry`
- Database access: PostgreSQL 16 via `psycopg` / SQLAlchemy, schema in [`../database/schema.sql`](../database/schema.sql)
