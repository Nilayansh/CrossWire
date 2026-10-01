from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Optional
from app.config import settings

Base = declarative_base()


def get_engine(db_url: Optional[str] = None):
    url = db_url or settings.DATABASE_URL
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(url, connect_args=connect_args)

    if url.startswith("sqlite") and not url.endswith(":memory:"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    return engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine=None):
    """Create all tables in the database."""
    e = target_engine or engine
    Base.metadata.create_all(bind=e)
