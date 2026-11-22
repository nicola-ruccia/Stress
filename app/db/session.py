import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

database_url = settings.DATABASE_URL.strip()
if database_url.startswith("postgres://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
elif database_url.startswith("postgresql://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]

if os.getenv("VERCEL") == "1" and database_url.startswith("sqlite:"):
    raise RuntimeError("Su Vercel configura DATABASE_URL con un database PostgreSQL persistente (es. Neon).")

engine_options = {"pool_pre_ping": True}
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite:") else {}
if database_url.startswith("postgresql+"):
    # Limita il pool per istanza serverless; usare la stringa pooled fornita dal provider.
    engine_options.update({"pool_size": 2, "max_overflow": 0, "pool_recycle": 300})

engine = create_engine(database_url, connect_args=connect_args, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models import entities  # noqa: F401
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(bind=engine)
        return

    # Il database pubblico contiene solo gli account. I dati operativi vivono
    # negli schemi tenant creati da bind_company_database().
    entities.Account.__table__.create(bind=engine, checkfirst=True)
