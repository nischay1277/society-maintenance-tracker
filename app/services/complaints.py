from datetime import datetime, timedelta, timezone

from app.config import settings
from app.models import Complaint, ComplaintStatus


def is_overdue(complaint: Complaint) -> bool:
    if complaint.status == ComplaintStatus.resolved:
        return False
    created_at = complaint.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - created_at
    return age > timedelta(days=settings.overdue_days)
