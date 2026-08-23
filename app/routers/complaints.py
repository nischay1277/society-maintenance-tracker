from datetime import date, datetime, time

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import case
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user, require_admin, require_resident
from app.models import Complaint, ComplaintHistory, ComplaintStatus, Priority, User
from app.schemas import ComplaintRead, ComplaintUpdate
from app.services.complaints import is_overdue
from app.services.email import send_email
from app.services.files import save_upload


router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def complaint_with_overdue(complaint: Complaint) -> ComplaintRead:
    data = ComplaintRead.model_validate(complaint)
    data.is_overdue = is_overdue(complaint)
    return data


@router.post("", response_model=ComplaintRead, status_code=status.HTTP_201_CREATED)
def create_complaint(
    category: str = Form(...),
    description: str = Form(...),
    photo: UploadFile | None = File(None),
    resident: User = Depends(require_resident),
    db: Session = Depends(get_db),
):
    try:
        photo_path = save_upload(photo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    complaint = Complaint(resident_id=resident.id, category=category, description=description, photo_path=photo_path)
    db.add(complaint)
    db.flush()
    db.add(
        ComplaintHistory(
            complaint_id=complaint.id,
            old_status=None,
            new_status=ComplaintStatus.open,
            actor_id=resident.id,
            note="Complaint created",
        )
    )
    db.commit()
    db.refresh(complaint)
    return complaint_with_overdue(complaint)


@router.get("/mine", response_model=list[ComplaintRead])
def my_complaints(resident: User = Depends(require_resident), db: Session = Depends(get_db)):
    complaints = (
        db.query(Complaint)
        .options(selectinload(Complaint.history))
        .filter(Complaint.resident_id == resident.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return [complaint_with_overdue(item) for item in complaints]


@router.get("", response_model=list[ComplaintRead])
def list_complaints(
    category: str | None = None,
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    created_on: date | None = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint).options(selectinload(Complaint.history))
    if category:
        query = query.filter(Complaint.category == category)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if priority:
        query = query.filter(Complaint.priority == priority)
    if created_on:
        start = datetime.combine(created_on, time.min)
        end = datetime.combine(created_on, time.max)
        query = query.filter(Complaint.created_at.between(start, end))

    overdue_rank = case((Complaint.status != ComplaintStatus.resolved, 0), else_=1)
    complaints = query.order_by(overdue_rank, Complaint.created_at.asc()).all()
    return sorted([complaint_with_overdue(item) for item in complaints], key=lambda item: (not item.is_overdue, item.created_at))


@router.patch("/{complaint_id}", response_model=ComplaintRead)
def update_complaint(
    complaint_id: int,
    payload: ComplaintUpdate,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).options(selectinload(Complaint.history)).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.status == ComplaintStatus.resolved:
        raise HTTPException(status_code=400, detail="Resolved complaints are closed")

    status_changed = payload.status is not None and payload.status != complaint.status
    if payload.priority is not None:
        complaint.priority = payload.priority

    if status_changed:
        old_status = complaint.status
        complaint.status = payload.status
        if payload.status == ComplaintStatus.resolved:
            complaint.resolved_at = datetime.utcnow()
        db.add(
            ComplaintHistory(
                complaint_id=complaint.id,
                old_status=old_status,
                new_status=payload.status,
                actor_id=admin.id,
                note=payload.note,
            )
        )
        background_tasks.add_task(
            send_email,
            complaint.resident.email,
            "Complaint status updated",
            f"Your complaint #{complaint.id} is now {payload.status.value}.\n\nNote: {payload.note or 'No note added.'}",
        )

    db.commit()
    db.refresh(complaint)
    return complaint_with_overdue(complaint)
