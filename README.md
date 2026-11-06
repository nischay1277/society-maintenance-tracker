# Society Maintenance Tracker

A FastAPI application for apartment-society complaint management. Residents submit complaints and view their history; admins manage status, priority, notices, and dashboard summaries. A small server-rendered browser interface is included for exercising the API.

## Features

- Resident registration and JWT login with resident/admin authorization checks.
- Complaint creation with optional photo uploads and per-resident complaint lists.
- Admin filters by category, status, priority, and creation date; overdue items appear first.
- Status history with actor, timestamp, old/new status, and optional note.
- Resolved complaints are closed to further updates.
- Notice board and email notifications for important notices and status changes.
- Configurable overdue threshold, SQLite persistence, and optional SMTP delivery.

## Tech Stack

- FastAPI
- SQLAlchemy
- SQLite by default, PostgreSQL compatible through `DATABASE_URL`
- JWT auth with resident/admin roles
- FastAPI file upload support
- SMTP email integration, with console logging when SMTP is not configured

## Setup

Use Python 3.10 or newer and run commands from the repository root. The application uses relative paths for templates, static files, the SQLite database, and uploads.

```bash
git clone https://github.com/nischay1277/society-maintenance-tracker.git
cd society-maintenance-tracker
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

macOS / Linux:

```bash
source .venv/bin/activate
cp .env.example .env
```

Edit `.env` before starting. Set a unique `SECRET_KEY` and replace the sample admin credentials. Then:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- App: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

When both `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set, startup creates the account if that email is absent. The sample `.env.example` uses these local-demo values:

- Email: `admin@example.com`
- Password: `Admin@123`

Changing `.env` does not reset the password of an existing database user. Registration always creates residents; use the startup configuration to create an admin. Database tables and the upload directory are created on startup.

## Environment Variables

See `.env.example`.

Important values:

- `DATABASE_URL`: database connection string; defaults to `sqlite:///./society.db`
- `SECRET_KEY`: JWT signing key
- `OVERDUE_DAYS`: number of days before unresolved complaints count as overdue
- `UPLOAD_DIR`: local folder for complaint photos
- `SMTP_*`: optional email service settings

Other settings include `ACCESS_TOKEN_EXPIRE_MINUTES` (default 120), `APP_NAME`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD`. `OVERDUE_DAYS` defaults to 7. SMTP delivery uses `SMTP_HOST`, `SMTP_PORT` (587 by default), `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and `SMTP_USE_TLS`.

PostgreSQL can be selected through `DATABASE_URL`, but its Python driver is not included in `requirements.txt`; install a compatible driver and use its SQLAlchemy URL. Schema creation uses `Base.metadata.create_all`, not versioned migrations.

## Database Schema

### users

Stores resident and admin accounts.

- `id`
- `name`
- `email`
- `flat_number`
- `phone`
- `hashed_password`
- `role`
- `created_at`

### complaints

Stores the current state of each complaint.

- `id`
- `resident_id`
- `category`
- `description`
- `photo_path`
- `status`
- `priority`
- `created_at`
- `updated_at`
- `resolved_at`

### complaint_history

Stores every status movement for auditability.

- `id`
- `complaint_id`
- `old_status`
- `new_status`
- `actor_id`
- `note`
- `created_at`

### notices

Stores notice board posts.

- `id`
- `title`
- `body`
- `is_important`
- `author_id`
- `created_at`

## API Summary

### Auth

- `POST /api/auth/register` - register resident
- `POST /api/auth/login` - login and receive JWT token
- `GET /api/auth/me` - current authenticated user

Login uses an OAuth2 form body (`application/x-www-form-urlencoded`): put the email in the `username` field and provide `password`. Other protected calls use `Authorization: Bearer <access_token>`. Complaint creation uses multipart form data; registration, notices, and admin updates use JSON.

### Complaints

- `POST /api/complaints` - resident creates complaint with optional photo
- `GET /api/complaints/mine` - resident views their complaints and history
- `GET /api/complaints` - admin lists complaints with filters
- `PATCH /api/complaints/{complaint_id}` - admin updates status, priority, and note

### Notices

- `POST /api/notices` - admin creates notice
- `GET /api/notices` - resident/admin views notices

### Dashboard

- `GET /api/dashboard` - admin summary by status, category, and overdue count

## Example Admin Update

```json
{
  "status": "In Progress",
  "priority": "High",
  "note": "Assigned to plumber"
}
```

## Try the workflow

1. Start the application and open `/docs` or the browser interface.
2. Register a resident, log in, and create a complaint with `category` and `description` (optional photo).
3. Log in as the configured admin, list complaints, and set status to `In Progress` with an optional note.
4. Check the resident's status history, dashboard totals, and notification output.
5. Resolve the complaint and confirm that subsequent admin updates are rejected.

The sample credentials above are placeholders for local testing, not a hosted demonstration account.

## Architecture and layout

```text
Browser / REST client -> FastAPI routers -> role checks -> SQLAlchemy -> database
                                      -> file service -> uploads/
                                      -> background tasks -> SMTP or console log
```

| Path | Responsibility |
| --- | --- |
| `app/main.py` | Startup schema/admin setup, API assembly, and static mounts |
| `app/models.py`, `app/schemas.py` | Database models and validated API representations |
| `app/security.py`, `app/dependencies.py` | Password hashing, JWTs, and role dependencies |
| `app/routers/` | Auth, complaints, notices, dashboard, and browser routes |
| `app/services/` | Overdue calculation, uploads, and email |
| `app/templates/`, `app/static/` | Browser interface |
| `.env.example` | Configuration template |

See [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for the existing design explanation.

## Implementation limits

- Email background tasks run in the API process and have no persistent retry queue. With no SMTP host, notification content is printed to the console instead of sent.
- Upload validation checks file extensions (`jpg`, `jpeg`, `png`, `webp`), not image content or a maximum file size. Uploaded files are served through a static mount rather than per-user download authorization.
- Overdue status is computed at request time; there is no scheduled overdue-email job.
- The repository does not include an automated test suite, deployment configuration, migration history, or measured load results. The workflow above is a manual smoke-check procedure.
- Replace demo secrets and credentials before exposing the application beyond a local environment. Keep `.env`, the database, and uploaded resident photos out of source control.
