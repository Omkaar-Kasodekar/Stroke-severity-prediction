import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    SmallInteger,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker


# Prefer an explicit DATABASE_URL environment variable. If not provided,
# fall back to a local SQLite file so tests and local runs don't require
# a separate Postgres server.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # file-based SQLite in project root
    db_path = Path(__file__).resolve().parent.parent / "stroke_cds.db"
    DATABASE_URL = f"sqlite+pysqlite:///{db_path}"

# Create engine with sqlite-specific connect args when appropriate
engine_kwargs = {"echo": False, "future": True}
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, **engine_kwargs)
else:
    engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    age = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)
    avg_glucose_level = Column(Float, nullable=False)
    hypertension = Column(SmallInteger, nullable=False)
    heart_disease = Column(SmallInteger, nullable=False)
    severity = Column(String(32), nullable=False)
    model = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

