"""
database.py

Configures the SQLAlchemy database engine, session maker, and Base class.
Defines a helper function to yield database sessions for API requests.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import os

# Put scanner.db in the user's App Data Directory (outside the workspace)
# to prevent VS Code Live Server from hot-reloading the browser on database updates.
db_dir = "C:\\Users\\LOQ\\.gemini\\antigravity"
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "scanner.db")
DATABASE_URL = f"sqlite:///{db_path}"

# connect_args={"check_same_thread": False} is required only for SQLite.
# By default, SQLite only allows one thread to communicate with it.
# FastAPI runs requests in multiple threads, so we must allow multi-threaded access.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal is the class we will instantiate to get a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models (it maps Python classes to SQL tables)
Base = declarative_base()


def get_db():
    """
    Dependency helper that yields a database session.
    Guarantees that the session is closed after the API request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
