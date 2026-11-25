from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# The engine is the connection to the database file.
# check_same_thread=False is needed for SQLite because FastAPI may use
# the connection from more than one thread.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

# SessionLocal() gives us a new database session.
# A session is our workspace for reading and saving rows.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
