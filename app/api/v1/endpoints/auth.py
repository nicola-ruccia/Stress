"""Autenticazione per le tre viste Semalìa e gestione inviti aziendali."""
from datetime import datetime, timedelta
import base64
import hashlib
import hmac
import json
import re
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import Account, Dipendente
from app.db.tenancy import bind_company_database
from app.core.privacy import pseudonimize_matricola
from app.schemas.schemas import (
    AccountBootstrapRequest, AccountInviteRequest, AccountInviteResponse,
    AccountLoginRequest, AccountLoginResponse, AccountSetupRequest, AccountSummary,
)

router = APIRouter()
ROLES = {"hr", "medico", "lavoratore"}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 254 or not EMAIL_RE.fullmatch(email):
        raise HTTPException(status_code=422, detail="Inserisci un indirizzo email valido.")
    return email


def _password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$" + base64.urlsafe_b64encode(salt + digest).decode()


def _check_password(password: str, stored: str | None) -> bool:
    if not stored or not stored.startswith("scrypt$"):
        return False
    raw = base64.urlsafe_b64decode(stored.split("$", 1)[1])
    salt, expected = raw[:16], raw[16:]
    actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return hmac.compare_digest(actual, expected)


def _token(account: Account) -> str:
    payload = {"sub": account.email, "role": account.role,
               "exp": int((datetime.utcnow() + timedelta(minutes=settings.AUTH_TOKEN_MINUTES)).timestamp())}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=")
    signature = hmac.new(settings.SECRET_KEY.encode(), body, hashlib.sha256).digest()
    return body.decode() + "." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


def current_account(authorization: str | None = Header(None), db: Session = Depends(get_db)) -> Account:
    unauthorized = HTTPException(status_code=401, detail="Sessione non valida o scaduta.", headers={"WWW-Authenticate": "Bearer"})
    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized
    try:
        body, signature = authorization[7:].split(".", 1)
        expected = base64.urlsafe_b64encode(hmac.new(settings.SECRET_KEY.encode(), body.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
        if not hmac.compare_digest(signature, expected):
            raise unauthorized
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        if payload["exp"] < int(datetime.utcnow().timestamp()):
            raise unauthorized
        account = db.query(Account).filter(Account.email == payload["sub"], Account.active.is_(True)).first()
        if not account or account.role != payload["role"]:
            raise unauthorized
        bind_company_database(db, account.company)
        return account
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise unauthorized


def require_hr(account: Account = Depends(current_account)) -> Account:
    if account.role != "hr":
        raise HTTPException(status_code=403, detail="Operazione riservata all'HR.")
    return account


def require_medico(account: Account = Depends(current_account)) -> Account:
    if account.role != "medico":
        raise HTTPException(status_code=403, detail="Operazione riservata al medico competente.")
    return account


def require_lavoratore(account: Account = Depends(current_account)) -> Account:
    if account.role != "lavoratore":
        raise HTTPException(status_code=403, detail="Operazione riservata al lavoratore.")
    return account


@router.post("/bootstrap-hr", response_model=AccountLoginResponse, summary="Crea l'account HR iniziale di una nuova azienda")
def bootstrap_hr(req: AccountBootstrapRequest, db: Session = Depends(get_db)):
    if not settings.HR_BOOTSTRAP_TOKEN or not hmac.compare_digest(req.bootstrap_token, settings.HR_BOOTSTRAP_TOKEN):
        raise HTTPException(status_code=403, detail="Bootstrap HR disabilitato o token non valido.")
    email = _normalize_email(req.email)
    if db.query(Account).filter(Account.email == email).first():
        raise HTTPException(status_code=409, detail="Esiste già un account con questa email.")
    company = " ".join(req.company.strip().casefold().split())
    if not company:
        raise HTTPException(status_code=422, detail="Il nome dell'azienda è obbligatorio.")
    account = Account(email=email, role="hr", company=company, password_hash=_password_hash(req.password))
    db.add(account)
    db.commit()
    db.refresh(account)
    return AccountLoginResponse(access_token=_token(account), role=account.role, email=account.email, company=account.company, employee_code=None)


@router.post("/invite", response_model=AccountInviteResponse, summary="Autorizza un indirizzo aziendale e genera il primo accesso")
def invite_account(req: AccountInviteRequest, hr: Account = Depends(require_hr), db: Session = Depends(get_db)):
    role = req.role.strip().lower()
    email = _normalize_email(req.email)
    if role not in ROLES:
        raise HTTPException(status_code=422, detail="Ruolo ammesso: hr, medico o lavoratore.")
    employee_code = None
    if role == "lavoratore":
        if not req.employee_identifier or not req.employee_identifier.strip():
            raise HTTPException(status_code=422, detail="Per il lavoratore serve la matricola presente nel workbook aziendale.")
        employee_code = pseudonimize_matricola(req.employee_identifier)
        if not db.query(Dipendente).filter(Dipendente.codice == employee_code).first():
            raise HTTPException(status_code=422, detail="Matricola non trovata nei dati aziendali caricati.")
    elif req.employee_identifier:
        raise HTTPException(status_code=422, detail="La matricola è ammessa solo per gli account lavoratore.")
    existing = db.query(Account).filter(Account.email == email).first()
    if existing:
        if existing.company != hr.company:
            raise HTTPException(status_code=409, detail="Email già associata a un'altra azienda.")
        if existing.password_hash:
            raise HTTPException(status_code=409, detail="Email già attivata; usa il flusso di recupero credenziali.")
        account = existing
    else:
        account = Account(email=email, role=role, employee_code=employee_code, company=hr.company)
        db.add(account)
    if account.role != role or account.employee_code != employee_code:
        raise HTTPException(status_code=409, detail="L'indirizzo risulta già autorizzato con un ruolo diverso.")
    setup_token = secrets.token_urlsafe(32)
    account.setup_token_hash = hashlib.sha256(setup_token.encode()).hexdigest()
    account.setup_expires_at = datetime.utcnow() + timedelta(hours=72)
    db.commit()
    return AccountInviteResponse(email=email, role=role, setup_token=setup_token,
                                 expires_at=account.setup_expires_at.isoformat() + "Z",
                                 delivery_note="Consegna questo link/token al dipendente tramite un canale aziendale verificato.")


@router.get("/accounts", response_model=list[AccountSummary], summary="Elenco account dell'azienda per HR")
def list_accounts(hr: Account = Depends(require_hr), db: Session = Depends(get_db)):
    return db.query(Account).filter(Account.company == hr.company).order_by(Account.email).all()


@router.delete("/accounts/{account_id}", summary="Disattiva un account aziendale")
def revoke_account(account_id: int, hr: Account = Depends(require_hr), db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id, Account.company == hr.company).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account aziendale non trovato.")
    if account.email == hr.email:
        raise HTTPException(status_code=409, detail="Non puoi disattivare il tuo account attivo.")
    if account.role == "hr":
        active_hr = db.query(Account).filter(Account.company == hr.company, Account.role == "hr", Account.active.is_(True)).count()
        if active_hr <= 1:
            raise HTTPException(status_code=409, detail="L'azienda deve mantenere almeno un account HR attivo.")
    account.active = False
    db.commit()
    return {"status": "disattivato", "account_id": account.id}


@router.post("/set-password", response_model=AccountLoginResponse, summary="Primo accesso: email autorizzata, token invito e password scelta dall'utente")
def set_password(req: AccountSetupRequest, db: Session = Depends(get_db)):
    email = _normalize_email(req.email)
    account = db.query(Account).filter(Account.email == email, Account.active.is_(True)).first()
    supplied_hash = hashlib.sha256(req.setup_token.encode()).hexdigest()
    if (not account or not account.setup_token_hash or not account.setup_expires_at
            or account.setup_expires_at < datetime.utcnow()
            or not hmac.compare_digest(account.setup_token_hash, supplied_hash)):
        raise HTTPException(status_code=400, detail="Invito non valido o scaduto; chiedi un nuovo invito all'HR.")
    account.password_hash = _password_hash(req.password)
    account.setup_token_hash = None
    account.setup_expires_at = None
    db.commit()
    return AccountLoginResponse(access_token=_token(account), role=account.role, email=account.email, company=account.company, employee_code=account.employee_code)


@router.post("/login", response_model=AccountLoginResponse, summary="Accessi successivi con email e password")
def login(req: AccountLoginRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.email == _normalize_email(req.email), Account.active.is_(True)).first()
    if not account or not _check_password(req.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Email o password non corretti.")
    return AccountLoginResponse(access_token=_token(account), role=account.role, email=account.email, company=account.company, employee_code=account.employee_code)
