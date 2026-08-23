from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import Notice, User, UserRole
from app.schemas import NoticeCreate, NoticeRead
from app.services.email import send_email


router = APIRouter(prefix="/api/notices", tags=["notices"])


@router.post("", response_model=NoticeRead, status_code=status.HTTP_201_CREATED)
def create_notice(
    payload: NoticeCreate,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    notice = Notice(title=payload.title, body=payload.body, is_important=payload.is_important, author_id=admin.id)
    db.add(notice)
    db.commit()
    db.refresh(notice)

    if notice.is_important:
        residents = db.query(User).filter(User.role == UserRole.resident).all()
        for resident in residents:
            background_tasks.add_task(
                send_email,
                resident.email,
                f"Important notice: {notice.title}",
                notice.body,
            )
    return notice


@router.get("", response_model=list[NoticeRead])
def list_notices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notice).order_by(Notice.is_important.desc(), Notice.created_at.desc()).all()
