from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import ComplaintStatus, Priority, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)
    flat_number: str | None = None
    phone: str | None = None


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    flat_number: str | None
    phone: str | None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class ComplaintHistoryRead(BaseModel):
    id: int
    old_status: ComplaintStatus | None
    new_status: ComplaintStatus
    actor_id: int
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintRead(BaseModel):
    id: int
    resident_id: int
    category: str
    description: str
    photo_path: str | None
    status: ComplaintStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    is_overdue: bool = False
    history: list[ComplaintHistoryRead] = []

    model_config = ConfigDict(from_attributes=True)


class ComplaintUpdate(BaseModel):
    status: ComplaintStatus | None = None
    priority: Priority | None = None
    note: str | None = None


class NoticeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=3)
    is_important: bool = False


class NoticeRead(BaseModel):
    id: int
    title: str
    body: str
    is_important: bool
    author_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    by_status: dict[str, int]
    by_category: dict[str, int]
    overdue_count: int
