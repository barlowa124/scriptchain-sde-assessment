# Email subscriber service

A web page saves a user's name and email address, then sends a confirmation
email to that address. The email body contains the user's name and the
address itself.

- `backend/`: FastAPI service with a REST API and SQLAlchemy persistence.
- `frontend/`: Angular (TypeScript) single-page form.

## API

| Method | Path | Body | Responses |
|--------|---------------------|----------------------------------------|------------------------------------|
| GET | `/api/health` | none | `200 {"status": "ok"}` |
| POST | `/api/subscribers` | `{"name": str, "email": str}` | `201` created, `409` duplicate, `422` invalid |

The email address is normalized to lowercase before it is stored. A duplicate
address returns `409` and sends no second email.

## Configuration

| Variable | Default | Purpose |
|-----------------|------------------------------------------------------|-------------------------------|
| `DATABASE_URL` | `mysql+pymysql://app:app@localhost:3306/subscribers` | SQLAlchemy URL for MySQL |
| `SMTP_HOST` | `localhost` | SMTP server for confirmations |
| `SMTP_PORT` | `1025` | SMTP port |
| `SMTP_FROM` | `noreply@example.test` | Sender address |

The temporary inbox used for testing is whatever SMTP server `SMTP_HOST` and
`SMTP_PORT` point to, for example a local capture server or a mail sandbox.

## Run the backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn sqlalchemy pymysql "pydantic[email]" email-validator
DATABASE_URL="mysql+pymysql://USER:PASS@localhost:3306/subscribers" \
  .venv/bin/uvicorn app.main:create_app --factory --port 8000
```

The tables are created on startup. The database itself must exist first.

## Run the frontend

```bash
cd frontend
npm install
npx ng serve
```

`proxy.conf.json` forwards `/api` to `http://localhost:8000`, so the Angular
page and the API can run on separate ports during development.

## Tests

```bash
cd backend
.venv/bin/pip install pytest httpx
.venv/bin/python -m pytest -q
```

The tests run against SQLite with a fake mailer.

## Verification status

The backend suite passes with `pytest`, 5 tests. The Angular production build
succeeds. A manual run against SQLite returned `201` for a new address. A repeat
returned `409`. An invalid address returned `422`. The `/api` proxy on the
dev server forwards requests to the backend.

MySQL was not exercised in this environment. The browser form was not tested.
