"""Database connection and setup for IB Assessment App."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Detect Railway production environment
# Railway sets RAILWAY_ENVIRONMENT, RAILWAY_PROJECT_ID, etc.
IS_RAILWAY = os.environ.get("RAILWAY_ENVIRONMENT") is not None

if IS_RAILWAY:
    # Production: Use Railway's persistent volume mount
    DATABASE_DIR = "/app/database"
    DATABASE_PATH = os.path.join(DATABASE_DIR, "ibac.db")
else:
    # Local development: Use relative path from project root
    DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
    DATABASE_PATH = os.path.join(DATABASE_DIR, "ib_assessment.db")

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Log database configuration
print(f"[database] IS_RAILWAY: {IS_RAILWAY}")
print(f"[database] DATABASE_DIR: {DATABASE_DIR}")
print(f"[database] DATABASE_PATH: {DATABASE_PATH}")

# Create engine with SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite with FastAPI
    echo=True  # Log SQL queries for debugging
)

# Enable foreign key support in SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    # Ensure database directory exists
    try:
        os.makedirs(DATABASE_DIR, exist_ok=True)
        print(f"[database] Directory ensured: {DATABASE_DIR}")
    except PermissionError as e:
        print(f"[database] WARNING: Cannot create directory {DATABASE_DIR}: {e}")
        print("[database] Assuming directory already exists (Railway volume mount)")

    # Import models to register them with Base
    from . import models  # noqa: F401

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DATABASE_PATH}")
