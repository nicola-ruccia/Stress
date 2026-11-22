"""Persist the employee mapping encrypted inside the current company database."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import ImportMapping


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.PSEUDO_KEY.encode("utf-8")).digest())
    return Fernet(key)


def store_mapping(db: Session, csv_text: str) -> None:
    encrypted = _fernet().encrypt(csv_text.encode("utf-8")).decode("ascii")
    db.query(ImportMapping).delete()
    db.add(ImportMapping(encrypted_csv=encrypted))
    db.commit()


def read_mapping(db: Session) -> str | None:
    row = db.query(ImportMapping).order_by(ImportMapping.created_at.desc(), ImportMapping.id.desc()).first()
    if not row:
        return None
    try:
        return _fernet().decrypt(row.encrypted_csv.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError):
        return None
