# Society Maintenance Tracker

Backend-focused FastAPI assignment for managing apartment society complaints, status history, overdue complaints, notices, and email updates.

## Tech Stack

- FastAPI
- SQLAlchemy
- SQLite by default, PostgreSQL compatible through `DATABASE_URL`
- JWT auth with resident/admin roles
- FastAPI file upload support
- SMTP email integration, with console logging when SMTP is not configured

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open:

- App: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

The default `.env.example` creates an admin account:

- Email: `admin@example.com`
- Password: `Admin@123`

## Environment Variables

See `.env.example`.

Important values:

- `DATABASE_URL`: database connection string
- `SECRET_KEY`: JWT signing key
- `OVERDUE_DAYS`: number of days before unresolved complaints count as overdue
- `UPLOAD_DIR`: local folder for complaint photos
- `SMTP_*`: optional email service settings

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

## Submission Notes

Submit the GitHub repository link only. Keep the frontend simple; grading should focus on backend structure, database design, API behavior, and documentation.
