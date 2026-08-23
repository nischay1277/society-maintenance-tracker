from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Complaint, ComplaintStatus, User
from app.schemas import DashboardSummary
from app.services.complaints import is_overdue


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
def dashboard(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    by_status = dict(
        db.query(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status).all()
    )
    by_category = dict(
        db.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
    )
    open_complaints = db.query(Complaint).filter(Complaint.status != ComplaintStatus.resolved).all()
    overdue_count = sum(1 for complaint in open_complaints if is_overdue(complaint))
    return DashboardSummary(
        by_status={str(key.value if hasattr(key, "value") else key): value for key, value in by_status.items()},
        by_category={str(key): value for key, value in by_category.items()},
        overdue_count=overdue_count,
    )
