# Finance Dashboard Backend

A RESTful backend API for a multi-role finance dashboard system, built with **Python + Flask** and **SQLite**. Supports user management, financial record CRUD, dashboard analytics, and JWT-based role access control.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Running](#setup--running)
- [Demo Credentials](#demo-credentials)
- [API Reference](#api-reference)
- [Role-Based Access Control](#role-based-access-control)
- [Design Decisions & Assumptions](#design-decisions--assumptions)

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Readable, widely used for backends |
| Framework | Flask 3.x | Lightweight, easy to understand |
| Database | SQLite (via stdlib `sqlite3`) | Zero-config, file-based, perfect for this scope |
| Auth | PyJWT + Werkzeug | JWT tokens + secure password hashing |
| Config | python-dotenv | Clean `.env`-based configuration |

**No heavy ORM or extra frameworks** — kept intentionally simple and transparent so every query is visible and understandable.

---

## Project Structure

```
finance_dashboard/
│
├── app/
│   ├── __init__.py            # Flask app factory (create_app)
│   ├── database.py            # SQLite connection + schema creation
│   │
│   ├── models/                # All DB operations (one file per entity)
│   │   ├── user.py            # User CRUD + password verification
│   │   └── record.py          # Record CRUD + dashboard aggregations
│   │
│   ├── middleware/            # Cross-cutting concerns
│   │   ├── auth.py            # JWT generation, @jwt_required, @roles_required
│   │   └── validators.py      # Input validation helpers
│   │
│   └── routes/                # HTTP route handlers (Blueprints)
│       ├── auth.py            # /api/auth/*
│       ├── users.py           # /api/users/*
│       ├── records.py         # /api/records/*
│       └── dashboard.py       # /api/dashboard/*
│
├── tests/
│   └── test_api.py            # Integration tests (Flask test client)
│
├── .env                       # Environment variables
├── run.py                     # Development server entry point
├── seed.py                    # Populates DB with demo data
└── requirements.txt           # Python dependencies
```

### Why This Structure?

- **`models/`** — Pure data layer. No Flask imports, no HTTP concepts. Just functions that talk to the DB.
- **`middleware/`** — Reusable decorators and validators that sit between HTTP and business logic.
- **`routes/`** — Thin handlers. They validate input, call model functions, return JSON. No SQL here.
- **`database.py`** — Single source of truth for the DB connection and schema.

This separation makes it easy to test, change, or extend any layer independently.

---

## Setup & Running

### 1. Clone / Download the project

```bash
cd finance_dashboard
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment (optional)

The `.env` file already has sensible defaults:

```env
SECRET_KEY=super-secret-jwt-key-change-in-prod
JWT_EXPIRY_HOURS=24
DATABASE_PATH=finance.db
```

Change `SECRET_KEY` before any real deployment.

### 5. Seed the database with demo data

```bash
python seed.py
```

This creates 3 users (admin, analyst, viewer) and 15 sample financial records.

### 6. Start the server

```bash
python run.py
```

Server starts at: `http://localhost:5000`

Health check: `GET http://localhost:5000/api/health`

---

## Demo Credentials

| Role | Username | Password | What they can do |
|---|---|---|---|
| Admin | `admin_user` | `admin123` | Everything |
| Analyst | `analyst_user` | `analyst123` | View records + dashboard |
| Viewer | `viewer_user` | `viewer123` | View records only |

---

## API Reference

All protected endpoints require the header:
```
Authorization: Bearer <token>
```

You get the token from `POST /api/auth/login`.

---

### Auth Endpoints

#### `POST /api/auth/register`
Create a new user account.

**Request body:**
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "secret123",
  "role": "viewer"
}
```
> `role` must be `viewer`, `analyst`, or `admin`. Defaults to `viewer`.

**Response `201`:**
```json
{
  "message": "Account created successfully.",
  "user": { "id": "...", "username": "john", "role": "viewer", ... }
}
```

**Error cases:** `400` (invalid input), `409` (username taken)

---

#### `POST /api/auth/login`
Log in and receive a JWT token.

**Request body:**
```json
{ "username": "admin_user", "password": "admin123" }
```

**Response `200`:**
```json
{
  "message": "Login successful.",
  "token": "eyJhbGci...",
  "user": { "id": "...", "username": "admin_user", "role": "admin" }
}
```

**Error cases:** `401` (wrong credentials), `403` (account deactivated)

---

#### `GET /api/auth/me`  🔒
Get your own profile. Any logged-in user.

**Response `200`:**
```json
{
  "user": { "id": "...", "username": "...", "role": "...", "is_active": 1 }
}
```

---

### Financial Records Endpoints

#### `GET /api/records/`  🔒 (viewer, analyst, admin)
List all records with optional filters and pagination.

**Query parameters:**
| Param | Example | Description |
|---|---|---|
| `type` | `income` | Filter by `income` or `expense` |
| `category` | `Salary` | Filter by category (partial match) |
| `date_from` | `2024-01-01` | Records on or after this date |
| `date_to` | `2024-03-31` | Records on or before this date |
| `page` | `1` | Page number (default: 1) |
| `per_page` | `20` | Records per page (default: 20, max: 100) |

**Response `200`:**
```json
{
  "records": [ { "id": "...", "amount": 5000, "type": "income", ... } ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

---

#### `POST /api/records/`  🔒 (admin only)
Create a new financial record.

**Request body:**
```json
{
  "amount": 5000,
  "type": "income",
  "category": "Salary",
  "date": "2024-01-15",
  "notes": "January salary"
}
```

**Response `201`:**
```json
{ "message": "Record created.", "record": { "id": "...", "amount": 5000, ... } }
```

**Validation rules:**
- `amount` — required, must be a positive number
- `type` — required, must be `income` or `expense`
- `category` — required, non-empty string
- `date` — required, must be valid ISO format `YYYY-MM-DD`
- `notes` — optional

---

#### `GET /api/records/<id>`  🔒 (viewer, analyst, admin)
Get a single record by ID.

**Response `200`:**
```json
{ "record": { "id": "...", "amount": 5000, "type": "income", ... } }
```

**Error:** `404` if not found or soft-deleted.

---

#### `PUT /api/records/<id>`  🔒 (admin only)
Update a record. Send only the fields you want to change.

**Request body (all optional):**
```json
{
  "amount": 6000,
  "type": "income",
  "category": "Bonus",
  "date": "2024-02-01",
  "notes": "Performance bonus"
}
```

**Response `200`:**
```json
{ "message": "Record updated.", "record": { ... } }
```

---

#### `DELETE /api/records/<id>`  🔒 (admin only)
Soft-delete a record (sets `is_deleted = 1`, data stays in DB).

**Response `200`:**
```json
{ "message": "Record deleted successfully." }
```

---

### Dashboard Endpoints

#### `GET /api/dashboard/summary`  🔒 (analyst, admin)
Returns aggregated financial analytics.

**Response `200`:**
```json
{
  "total_income": 14300.00,
  "total_expenses": 3550.00,
  "net_balance": 10750.00,
  "by_category": [
    { "category": "Salary", "type": "income", "total": 10000.0, "count": 2 },
    { "category": "Rent",   "type": "expense","total": 2400.0,  "count": 2 }
  ],
  "monthly_trends": [
    { "month": "2024-03", "income": 6500.0, "expenses": 1620.0 },
    { "month": "2024-02", "income": 5800.0, "expenses": 1650.0 }
  ],
  "recent_activity": [ { "id": "...", "amount": 120.0, ... } ]
}
```

---

### User Management Endpoints

#### `GET /api/users/`  🔒 (admin only)
List all users in the system.

**Response `200`:**
```json
{ "users": [ { "id": "...", "username": "...", "role": "viewer", ... } ], "total": 3 }
```

---

#### `GET /api/users/<id>`  🔒 (admin only)
Get a single user by ID.

---

#### `PUT /api/users/<id>`  🔒 (admin only)
Update a user's role or active status.

**Request body:**
```json
{ "role": "analyst" }
```
or
```json
{ "is_active": false }
```

**Response `200`:**
```json
{ "message": "User updated.", "user": { ... } }
```

---

### Health Check

#### `GET /api/health`  (public)
```json
{ "status": "ok", "service": "Finance Dashboard API" }
```

---

## Role-Based Access Control

| Endpoint | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| Register / Login | ✓ | ✓ | ✓ |
| GET /auth/me | ✓ | ✓ | ✓ |
| GET /records/ | ✓ | ✓ | ✓ |
| GET /records/:id | ✓ | ✓ | ✓ |
| POST /records/ | ✗ | ✗ | ✓ |
| PUT /records/:id | ✗ | ✗ | ✓ |
| DELETE /records/:id | ✗ | ✗ | ✓ |
| GET /dashboard/summary | ✗ | ✓ | ✓ |
| GET /users/ | ✗ | ✗ | ✓ |
| PUT /users/:id | ✗ | ✗ | ✓ |

**How it works:**

The `@jwt_required` decorator (in `middleware/auth.py`) verifies the JWT on every protected request and loads the user into `flask.g`. The `@roles_required("admin")` decorator wraps `@jwt_required` and additionally checks the role — returning `403 Forbidden` if the user's role isn't in the allowed list.

```python
# Example from routes/records.py
@records_bp.post("/")
@roles_required("admin")          # Only admins can create records
def create():
    ...
```

---

## Design Decisions & Assumptions

### 1. No ORM (raw sqlite3)
I chose raw `sqlite3` over SQLAlchemy to keep the project transparent and dependency-light. Every SQL query is visible and easy to follow. For a larger project, an ORM would be the right call.

### 2. Soft Deletes
Records are never truly deleted — they get `is_deleted = 1`. This preserves data integrity for auditing and historical analytics. The dashboard aggregations automatically exclude soft-deleted records.

### 3. JWT Authentication (stateless)
Tokens are self-contained and expire after 24 hours (configurable via `.env`). There's no token revocation — a logged-out token remains valid until expiry. For production, a token blacklist or short expiry + refresh token pattern would be used.

### 4. Passwords
Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2-SHA256 by default). Plain passwords are never stored or logged.

### 5. Assumptions Made
- A single admin can manage all records (no per-user record ownership restrictions for now)
- Amounts are stored as floats (REAL in SQLite). For real finance apps, integers in the smallest currency unit (paise) are safer to avoid floating point errors
- Dates are stored as ISO strings (YYYY-MM-DD) which sort correctly alphabetically
- `updated_at` is only set when a record is updated, not automatically by the DB trigger (SQLite doesn't support `ON UPDATE` triggers natively in a cross-platform way)

### 6. What I'd Add for Production
- Refresh tokens + token blacklist on logout
- Rate limiting per IP/user
- Pagination cursors instead of offset-based (more efficient at scale)
- Amounts stored as integers (paise/cents) instead of floats
- Proper migration system (e.g. Alembic)
- Structured logging
- Docker + docker-compose setup
