"""Create three disposable judge accounts and synthetic company data.

Run explicitly with `python scripts/seed_judge_accounts.py --create-demo` after
configuring DATABASE_URL, SECRET_KEY and PSEUDO_KEY for the target database.
The credentials are intentionally public and must only be used with fake data.
"""
import argparse
import os
import sys
from pathlib import Path

# Allow invocation by file path from the repository root on Windows and Vercel.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load an optional Vercel environment file before importing application settings.
_env_parser = argparse.ArgumentParser(add_help=False)
_env_parser.add_argument("--env-file")
_env_args, _ = _env_parser.parse_known_args()
if _env_args.env_file:
    from dotenv import dotenv_values, load_dotenv

    if not dotenv_values(_env_args.env_file).get("DATABASE_URL"):
        raise SystemExit(
            "Il file ambiente non contiene DATABASE_URL; verifica il file scelto "
            "prima di eseguire il seed."
        )
    load_dotenv(_env_args.env_file, override=True)

from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import _password_hash
from app.core.config import settings
from app.core.privacy import pseudonimize_matricola
from app.db.session import SessionLocal, init_db
from app.db.tenancy import bind_company_database
from app.models.entities import Account, Dipendente
from app.services.dataset_generator import build_dataset_dataframes, genera_dataset_demo


COMPANY = "semalia-demo-giudici"
PASSWORDS = {
    "hr": "SemaliaHR2026!",
    "medico": "SemaliaMedico2026!",
    "lavoratore": "SemaliaStaff2026!",
}
EMAILS = {
    "hr": "giudice.hr@demo.semalia.it",
    "medico": "giudice.medico@demo.semalia.it",
    "lavoratore": "giudice.dipendente@demo.semalia.it",
}


def seed(db: Session, company: str = COMPANY) -> None:
    # Set before calling the generator so it never attempts to write demo files
    # into a serverless filesystem.
    os.environ["VERCEL"] = "1"

    for role, email in EMAILS.items():
        account = db.query(Account).filter(Account.email == email).first()
        if account and account.company != company:
            raise RuntimeError(f"L'indirizzo {email} è già assegnato a un'altra azienda.")
        if account and account.role != role:
            raise RuntimeError(f"L'indirizzo {email} esiste con un ruolo diverso.")

    # Create the company and its tenant schema before inserting demo data.
    bind_company_database(db, company)
    first_matricola = str(build_dataset_dataframes()["dipendenti"].iloc[0]["matricola"])
    worker_code = pseudonimize_matricola(first_matricola)
    if not db.query(Dipendente).filter(Dipendente.codice == worker_code).first():
        if db.query(Dipendente).count():
            raise RuntimeError(
                "Il database demo contiene già dati non riconosciuti; non li sovrascrivo. "
                "Usa un database aziendale demo vuoto."
            )
        genera_dataset_demo(db)

    for role, email in EMAILS.items():
        account = db.query(Account).filter(Account.email == email).first()
        if account is None:
            account = Account(email=email, role=role, company=company)
            db.add(account)
        account.role = role
        account.company = company
        account.employee_code = worker_code if role == "lavoratore" else None
        account.password_hash = _password_hash(PASSWORDS[role])
        account.setup_token_hash = None
        account.setup_expires_at = None
        account.active = True
    db.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea account pubblici per la demo giudici Semalìa.")
    parser.add_argument(
        "--create-demo", action="store_true",
        help="conferma la creazione/aggiornamento degli account demo e del dataset sintetico",
    )
    parser.add_argument("--env-file", help="file .env opzionale per selezionare il database target")
    parser.add_argument("--company", default=COMPANY, help="nome dell'azienda demo nel database selezionato")
    args = parser.parse_args()
    if not args.create_demo:
        parser.error("aggiungi --create-demo per confermare l'operazione sul database configurato")
    invalid_secret_values = {"", "[SENSITIVE]", "dev_secret_key_change_in_production"}
    invalid_pseudo_values = {"", "[SENSITIVE]", "chiave_segreta_hmac_sanita_privata_demo"}
    if (settings.SECRET_KEY in invalid_secret_values
            or settings.PSEUDO_KEY in invalid_pseudo_values):
        print("Errore: configura SECRET_KEY e PSEUDO_KEY prima di procedere.", file=sys.stderr)
        return 2
    if args.env_file and not settings.DATABASE_URL.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        print("Errore: il file produzione deve puntare a un database PostgreSQL.", file=sys.stderr)
        return 2

    init_db()
    with SessionLocal() as db:
        seed(db, company=args.company.strip().casefold())
    print("Account giudici creati/aggiornati. Tutti usano dati esclusivamente sintetici.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
