from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL, ensure_directories


ensure_directories()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 60},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


@event.listens_for(engine, "connect")
def configure_sqlite(connection, _):
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_schema() -> None:
    with engine.begin() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(plans)").fetchall()}
        if "content_version" not in existing:
            conn.exec_driver_sql("ALTER TABLE plans ADD COLUMN content_version INTEGER DEFAULT 1")
        if "content_source_mode" not in existing:
            conn.exec_driver_sql("ALTER TABLE plans ADD COLUMN content_source_mode VARCHAR(32) DEFAULT 'database'")
