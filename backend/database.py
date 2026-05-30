from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)


# Nullable columns added after the tables already existed in production.
# create_all() never ALTERs existing tables, so we add them idempotently here.
_MIGRATIONS = (
    'ALTER TABLE team ADD COLUMN IF NOT EXISTS icon VARCHAR',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS home_score INTEGER',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS away_score INTEGER',
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    with engine.begin() as conn:
        for stmt in _MIGRATIONS:
            conn.execute(text(stmt))


def get_session():
    with Session(engine) as session:
        yield session
