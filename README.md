# Smart City Parking System — Project B

Laboratory project for **Network Issues in Mobile Systems (L1)**, instructor Marcin Kacprowicz.
Author: **Yiğit Demir** (student ID 56442), Computer Science, 4th year / 7th semester.
Individual project (approved by the instructor).

A driver finds the nearest parking facility with a free space, **holds** a space for 10 minutes,
confirms it with a **simulated** payment (no real money) and views the reservation history.
An administrator manages facilities and spaces. The system is designed for unreliable mobile
connectivity: every data-changing request has a stable **operationId**, so a lost response can be
recovered and a retry never applies a change twice.

## Chosen topic and technologies

| Layer | Technology |
|---|---|
| Mobile client | Flutter (Dart), Android target, SQLite cache |
| Web service | Python 3.12, FastAPI, JWT |
| Database | PostgreSQL 16 (`btree_gist`, `pgcrypto`) |
| API contract | OpenAPI 3.0.3 — [`api/openapi.yaml`](api/openapi.yaml) |
| Diagrams | Mermaid sources — [`docs/diagrams/`](docs/diagrams) |

## Repository structure

```text
api/openapi.yaml                 API contract (M1)
database/schema.sql              tables, keys, constraints (M1)
database/seed.sql                simulated city data (Łódź)
database/tests/constraints_test.sql   checks double booking, idempotency, single payment
docs/network-scenarios.csv|.md   requirements & network-scenario matrix (26 test cases)
docs/diagrams/*.mmd / *.png      use case, class, ERD, architecture, sequences, state machine
docs/report/                     M1 report following Project_Documentation_Template_EN.docx (source, DOCX, PDF, build script)
docs/design-changes.md           design changes since M1
service/                         web service (from Lab 5)
mobile/                          Flutter client (from M2)
docker-compose.yml               reproducible database startup
```

## Startup (database, M1)

**Option A – Docker**

```bash
docker compose up -d db
# schema.sql and seed.sql are loaded automatically on the first start
docker compose exec db psql -U parking -d parking -c "\dt"
```

To reload from scratch: `docker compose down -v && docker compose up -d db`.

**Option B – local PostgreSQL 16**

```bash
createdb parking
psql -d parking -v ON_ERROR_STOP=1 -f database/schema.sql
psql -d parking -v ON_ERROR_STOP=1 -f database/seed.sql
```

**Run the design checks** (on a fresh database, after schema + seed):

```bash
psql -d parking -f database/tests/constraints_test.sql
# expected: OK 1 ... OK 6
```

## Regenerating documentation

```bash
# diagrams (needs @mermaid-js/mermaid-cli)
for f in docs/diagrams/*.mmd; do mmdc -i "$f" -o "${f%.mmd}.png" -s 2 -b white; done
# report DOCX + PDF (needs pandoc, LibreOffice, python-docx)
python3 docs/report/build_report.py
```

## Milestones

| Milestone | Content | Status |
|---|---|---|
| M1 | Analysis and conceptual design | done – tag `m1` |
| Lab 5 | Web service and database foundation | next |
| M2 | Client–server prototype | planned |
| M3 | Network resilience (scenarios NS-01…NS-26) | planned |
| Final | Final system and defence | planned |
