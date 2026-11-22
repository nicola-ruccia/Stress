"""Database-per-company routing for business data; credentials stay centralized."""
import hashlib
from pathlib import Path
from threading import Lock

from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import BASE_DIR, settings
from app.db.session import Base, engine as central_engine
from app.models.entities import (
    Account, Aggressione, Assenza, AuditLog, Checkin, Dipendente, EventoHR,
    ImportHistory, ImportMapping, Occupazione, OreMese, PresaInCarico, Turno,
)

_engines: dict[str, Engine] = {}
_lock = Lock()
TENANT_MODELS = (
    Dipendente, Turno, Assenza, OreMese, EventoHR, Aggressione, Occupazione,
    Checkin, PresaInCarico, AuditLog, ImportHistory,
    ImportMapping,
)


def bind_company_database(db: Session, company: str) -> None:
    """Route company data to a SQLite file locally or a PostgreSQL schema on Vercel."""
    company_key = company.strip().casefold()
    if not company_key:
        raise RuntimeError("Account senza azienda associata.")
    with _lock:
        tenant_engine = _engines.get(company_key)
        if tenant_engine is None:
            tenant_digest = hashlib.sha256(company_key.encode("utf-8")).hexdigest()
            if central_engine.dialect.name == "sqlite":
                folder = BASE_DIR / "data" / "tenants"
                folder.mkdir(parents=True, exist_ok=True)
                filename = tenant_digest + ".db"
                tenant_engine = create_engine(
                    f"sqlite:///{(folder / filename).as_posix()}",
                    connect_args={"check_same_thread": False}, pool_pre_ping=True,
                )
            elif central_engine.dialect.name == "postgresql":
                schema_name = "tenant_" + tenant_digest[:32]
                with central_engine.begin() as connection:
                    connection.execute(CreateSchema(schema_name, if_not_exists=True))
                tenant_engine = central_engine.execution_options(schema_translate_map={None: schema_name})
            else:
                raise RuntimeError("DATABASE_URL deve puntare a SQLite locale o PostgreSQL in produzione.")
            Base.metadata.create_all(bind=tenant_engine)
            _engines[company_key] = tenant_engine
    for model in TENANT_MODELS:
        db.bind_mapper(model.__mapper__, tenant_engine)
    # Account records remain in the central auth DB.
    db.bind_mapper(Account.__mapper__, central_engine)
