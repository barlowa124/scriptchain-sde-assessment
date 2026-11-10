import os
from email.message import EmailMessage
from smtplib import SMTP

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(320), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class SubscriberIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr


class SubscriberOut(BaseModel):
    id: int
    name: str
    email: str


def build_engine(url: str):
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def send_confirmation(to_address: str, name: str) -> None:
    """Send the confirmation email. Uses SMTP settings from the environment."""
    host = os.environ.get("SMTP_HOST", "localhost")
    port = int(os.environ.get("SMTP_PORT", "1025"))
    sender = os.environ.get("SMTP_FROM", "noreply@example.test")

    msg = EmailMessage()
    msg["Subject"] = "Please confirm your email address"
    msg["From"] = sender
    msg["To"] = to_address
    msg.set_content(
        f"Hi {name},\n\n"
        f"Thanks for signing up. This confirmation was sent to {to_address}.\n"
    )
    with SMTP(host, port, timeout=10) as smtp:
        smtp.send_message(msg)


def create_app(
    database_url: str | None = None,
    mailer=send_confirmation,
) -> FastAPI:
    url = database_url or os.environ.get(
        "DATABASE_URL", "mysql+pymysql://app:app@localhost:3306/subscribers"
    )
    engine = build_engine(url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    app = FastAPI(title="Email subscriber service")
    app.state.mailer = mailer

    def get_db():
        db: Session = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.post(
        "/api/subscribers",
        response_model=SubscriberOut,
        status_code=status.HTTP_201_CREATED,
    )
    def create_subscriber(payload: SubscriberIn, db: Session = Depends(get_db)):
        email = payload.email.lower()
        if db.query(Subscriber).filter(Subscriber.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email address is already subscribed.",
            )
        row = Subscriber(name=payload.name.strip(), email=email)
        db.add(row)
        db.commit()
        db.refresh(row)
        app.state.mailer(row.email, row.name)
        return SubscriberOut(id=row.id, name=row.name, email=row.email)

    return app
