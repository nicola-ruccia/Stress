from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.session import Base

class Dipendente(Base):
    """
    Persona pseudonimizzata. La matricola NON viene mai registrata qui.
    """
    __tablename__ = "dipendenti"

    codice = Column(String(10), primary_key=True, index=True)
    reparto = Column(String(50), nullable=False, index=True)
    ruolo = Column(String(50), nullable=False)  # infermiere, OSS, medico, altro
    data_assunzione = Column(Date, nullable=False)
    data_cessazione = Column(Date, nullable=True)
    tipo_cessazione = Column(String(50), nullable=True)  # dimissioni, altro

    turni = relationship("Turno", back_populates="dipendente", cascade="all, delete-orphan")
    assenze = relationship("Assenza", back_populates="dipendente", cascade="all, delete-orphan")
    ore_mese = relationship("OreMese", back_populates="dipendente", cascade="all, delete-orphan")
    eventi_hr = relationship("EventoHR", back_populates="dipendente", cascade="all, delete-orphan")
    checkins = relationship("Checkin", back_populates="dipendente", cascade="all, delete-orphan")
    presa_in_carico = relationship("PresaInCarico", back_populates="dipendente", uselist=False, cascade="all, delete-orphan")

class Turno(Base):
    __tablename__ = "turni"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codice = Column(String(10), ForeignKey("dipendenti.codice"), nullable=False, index=True)
    reparto = Column(String(50), nullable=False, index=True)
    inizio = Column(DateTime, nullable=False, index=True)
    fine = Column(DateTime, nullable=False)

    dipendente = relationship("Dipendente", back_populates="turni")

class Assenza(Base):
    __tablename__ = "assenze"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codice = Column(String(10), ForeignKey("dipendenti.codice"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # malattia, infortunio, ferie, altro
    data_inizio = Column(Date, nullable=False, index=True)
    data_fine = Column(Date, nullable=False)

    dipendente = relationship("Dipendente", back_populates="assenze")

class OreMese(Base):
    __tablename__ = "ore_mese"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codice = Column(String(10), ForeignKey("dipendenti.codice"), nullable=False, index=True)
    mese = Column(String(7), nullable=False, index=True)  # YYYY-MM
    ore_straordinario = Column(Float, default=0.0)
    ferie_residue_giorni = Column(Float, default=0.0)

    dipendente = relationship("Dipendente", back_populates="ore_mese")

class EventoHR(Base):
    __tablename__ = "eventi_hr"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codice = Column(String(10), ForeignKey("dipendenti.codice"), nullable=False, index=True)
    data = Column(Date, nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # richiesta_trasferimento, procedimento_disciplinare

    dipendente = relationship("Dipendente", back_populates="eventi_hr")

class Aggressione(Base):
    """
    Segnalazioni di aggressione: nessun dato personale del dipendente o del paziente.
    """
    __tablename__ = "aggressioni"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reparto = Column(String(50), nullable=False, index=True)
    data = Column(Date, nullable=False, index=True)

class Occupazione(Base):
    """
    Occupazione posti letto e pazienti presenti per reparto e data.
    """
    __tablename__ = "occupazione"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reparto = Column(String(50), nullable=False, index=True)
    data = Column(Date, nullable=False, index=True)
    pazienti_presenti = Column(Integer, nullable=False, default=0)

class Checkin(Base):
    """
    Check-in compilato direttamente dal lavoratore.
    """
    __tablename__ = "checkin"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codice = Column(String(10), ForeignKey("dipendenti.codice"), nullable=False, index=True)
    data = Column(Date, nullable=False, default=date.today, index=True)
    domanda_singola = Column(Integer, nullable=False)  # 1..5 (>=3 = sintomi Somalìa)
    bat12_punteggio = Column(Float, nullable=True)  # media 1..5
    bat12_dettaglio = Column(Text, nullable=True)  # JSON con risposte ai 12 item
    consenso_medico = Column(Boolean, nullable=False, default=False)  # Consenso esplicito, revocabile
    richiesta_colloquio = Column(Boolean, nullable=False, default=False)

    dipendente = relationship("Dipendente", back_populates="checkins")

class PresaInCarico(Base):
    """
    Registrazione della presa in carico da parte del Medico Competente / Psicologo.
    Alimenta il conteggio visibile all'HR (in forma anonima aggregata).
    """
    __tablename__ = "prese_in_carico"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codice = Column(String(10), ForeignKey("dipendenti.codice"), unique=True, nullable=False, index=True)
    data_presa_in_carico = Column(DateTime, nullable=False, default=datetime.utcnow)
    stato = Column(String(50), nullable=False, default="contattato")  # contattato, in_valutazione, concluso
    note = Column(Text, nullable=True)
    medico_id = Column(String(50), default="medico_competente")

    dipendente = relationship("Dipendente", back_populates="presa_in_carico")

class AuditLog(Base):
    """
    Registro degli accessi: obbligo di trasparenza GDPR e tutela privacy.
    Traccia ogni apertura di scheda individuale da parte del medico o admin.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    utente_id = Column(String(50), nullable=False)
    ruolo = Column(String(50), nullable=False)
    azione = Column(String(100), nullable=False)
    target_codice = Column(String(10), nullable=True, index=True)
    note = Column(Text, nullable=True)

class ImportHistory(Base):
    """
    Storico importazioni file Excel e report validazione.
    """
    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    nome_file = Column(String(255), nullable=False)
    righe_accettate = Column(Integer, nullable=False, default=0)
    righe_scartate = Column(Integer, nullable=False, default=0)
    report_json = Column(Text, nullable=True)

class ImportMapping(Base):
    """Mapping raw matricole/codici pseudonimi, cifrato e confinato al tenant."""
    __tablename__ = "import_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    encrypted_csv = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

class Account(Base):
    """Credenziali e associazione verificata a un ruolo aziendale."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), nullable=False, unique=True, index=True)
    role = Column(String(20), nullable=False, index=True)
    # Codice conservato nel database isolato dell'azienda (non nel DB centrale auth).
    employee_code = Column(String(10), nullable=True)
    company = Column(String(120), nullable=False)
    password_hash = Column(String(256), nullable=True)
    setup_token_hash = Column(String(64), nullable=True)
    setup_expires_at = Column(DateTime, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
