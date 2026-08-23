# System Design

The system uses FastAPI as the backend API layer and SQLAlchemy for the data model. Users are separated into two roles: resident and admin. Residents can register, log in, create complaints, upload an optional photo, view their own complaints, and read notices. Admins can view all complaints, filter them, assign priority, update complaint status, create notices, and view dashboard counts.

The complaint model stores the current complaint state, while the complaint history model stores the audit trail. This separation keeps list queries simple because the current status and priority are available on the complaint row. Every status change creates a complaint history record with the old status, new status, actor, timestamp, and optional note. When a complaint is created, an initial history row is also created with the new status set to Open. Once a complaint reaches Resolved, the API blocks further updates and stores the resolved timestamp.

Overdue detection is configurable through `OVERDUE_DAYS`. A complaint is overdue when it is not Resolved and its creation date is older than the configured threshold. The API computes this dynamically so the database does not need a scheduled job for a student-level project. The admin complaint list sorts overdue complaints to the top, and the dashboard counts unresolved complaints that cross the threshold.

Photo upload uses FastAPI's `UploadFile`. The implementation validates a small set of image extensions and stores the file in the configured upload directory. The database stores only the public path. For production, this can be replaced with Cloudinary, Firebase Storage, or S3 without changing the complaint schema much.

Notifications are sent through a small email service. When SMTP settings are configured, the service sends mail through the configured provider. If SMTP is not configured, it logs the email to the console, which keeps local setup simple. Status updates trigger an email to the complaint owner. Important notices trigger an email to all residents using FastAPI background tasks, so the API response is not blocked by the email work.

The frontend is intentionally minimal. It exists only to test login, complaint creation, complaint lists, notices, and dashboard calls. The main evaluation areas are the API design, role-based auth, database schema, complaint lifecycle, overdue logic, photo handling, and documentation.
