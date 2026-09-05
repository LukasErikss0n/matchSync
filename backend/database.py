from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)


_MIGRATIONS = (
    'ALTER TABLE team ADD COLUMN IF NOT EXISTS icon VARCHAR',
    'ALTER TABLE team ADD COLUMN IF NOT EXISTS icon_data BYTEA',
    'ALTER TABLE team ADD COLUMN IF NOT EXISTS crest_checked BOOLEAN NOT NULL DEFAULT FALSE',
    'ALTER TABLE team DROP COLUMN IF EXISTS color',
    'ALTER TABLE team DROP COLUMN IF EXISTS icon_cropped',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS home_score INTEGER',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS away_score INTEGER',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS is_playoff BOOLEAN NOT NULL DEFAULT FALSE',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS overtime BOOLEAN NOT NULL DEFAULT FALSE',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS shootout BOOLEAN NOT NULL DEFAULT FALSE',
    'ALTER TABLE "match" ADD COLUMN IF NOT EXISTS status VARCHAR',
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    with engine.begin() as conn:
        for stmt in _MIGRATIONS:
            conn.execute(text(stmt))


def get_session():
    with Session(engine) as session:
        yield session
