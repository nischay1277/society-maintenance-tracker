from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import User, UserRole
from app.routers import auth, complaints, dashboard, notices, web
from app.security import get_password_hash


def create_default_admin() -> None:
    if not settings.admin_email or not settings.admin_password:
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.admin_email).first()
        if existing:
            return
        admin = User(
            name="Default Admin",
            email=settings.admin_email,
            role=UserRole.admin,
            hashed_password=get_password_hash(settings.admin_password),
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
create_default_admin()

app = FastAPI(title=settings.app_name)
app.mount(f"/{settings.upload_dir}", StaticFiles(directory=settings.upload_dir), name="uploads")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web.router)
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(notices.router)
app.include_router(dashboard.router)
