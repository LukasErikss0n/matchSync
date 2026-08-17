from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)


# Nullable columns added after the tables already existed in production.
# create_all() never ALTERs existing tables, so we add them idempotently here.
_MIGRATIONS = (
    'ALTER TABLE team ADD COLUMN IF NOT EXISTS icon VARCHAR',
    'ALTER TABLE team ADD COLUMN IF NOT EXISTS color VARCHAR',
    'ALTER TABLE team ADD COLUMN IF NOT EXISTS icon_data BYTEA',
    # Superseded by icon_data: crests were briefly stored as base64 data URIs
    # and inlined into match JSON, which pushed a single response to ~700KB.
    # Purely derived from team.icon, so dropping it loses nothing the fetcher
    # can't rebuild.
    'ALTER TABLE team DROP COLUMN IF EXISTS icon_cropped',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS home_score INTEGER',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS away_score INTEGER',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS is_playoff BOOLEAN NOT NULL DEFAULT FALSE',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS overtime BOOLEAN NOT NULL DEFAULT FALSE',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS shootout BOOLEAN NOT NULL DEFAULT FALSE',
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    with engine.begin() as conn:
        for stmt in _MIGRATIONS:
            conn.execute(text(stmt))


def get_session():
    with Session(engine) as session:
        yield session
