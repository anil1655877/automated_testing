import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "data" / "qa_platform.sqlite"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Database Engine Setup
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(session_factory)

Base = declarative_base()

class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    total_pages = Column(Integer, default=0)
    total_bugs = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    
    bugs = relationship("Bug", back_populates="scan", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="scan", cascade="all, delete-orphan")

class Bug(Base):
    __tablename__ = "bugs"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False) # UI, API, CONSOLE, RESOURCE, PERFORMANCE
    severity = Column(String, nullable=False) # CRITICAL, HIGH, MEDIUM, LOW
    page_url = Column(String, nullable=True)
    xpath_or_selector = Column(String, nullable=True)
    screenshot_path = Column(String, nullable=True)
    root_cause = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    approved = Column(Boolean, default=False)
    
    scan = relationship("Scan", back_populates="bugs")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    target_channel = Column(String, nullable=False) # Slack, Email, Teams
    message = Column(Text, nullable=False)
    status = Column(String, default="SENT") # SENT, FAILED
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    scan = relationship("Scan", back_populates="notifications")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()
