from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import (
    OperatoreRischio,
    MedicoSchedaResponse,
    PresaInCaricoRequest,
    PresaInCaricoResponse,
)
from app.services.analytics import (
    compute_medico_dashboard,
    get_operatore_scheda_medico,
)
from app.models.entities import Account, PresaInCarico, AuditLog, Checkin
from app.api.v1.endpoints.auth import require_medico

router = APIRouter()

@router.get("/operatori", response_model=List[OperatoreRischio], summary="Elenco operatori per il Medico Competente")
def get_operatori_medico(
    reparto: Optional[str] = Query(None, description="Filtro per reparto"),
    mese: Optional[str] = Query(None, description="Mese YYYY-MM"),
    db: Session = Depends(get_db),
):
    try:
        operatori = compute_medico_dashboard(db, reparto_filtro=reparto, target_mese=mese)
        return operatori
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore recupero lista operatori: {str(e)}",
        )

@router.get("/operatore/{codice}", response_model=MedicoSchedaResponse, summary="Scheda clinico-organizzativa dell'operatore")
def get_scheda_operatore(
    codice: str,
    account: Account = Depends(require_medico),
    db: Session = Depends(get_db),
):
    medico_id = account.email
    scheda = get_operatore_scheda_medico(db, codice)
    if not scheda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operatore con codice '{codice}' non trovato.",
        )

    # Scrivi record nel Registro degli Accessi (Audit Log) a tutela GDPR
    audit_entry = AuditLog(
        utente_id=medico_id,
        ruolo="medico",
        azione="visualizzazione_scheda_individuale",
        target_codice=codice,
        note=f"Apertura scheda individuale operatore {codice}",
    )
    db.add(audit_entry)
    db.commit()

    return scheda

@router.post("/presa-in-carico/{codice}", response_model=PresaInCaricoResponse, summary="Registra o aggiorna la presa in carico")
def registra_presa_in_carico(
    codice: str,
    req: PresaInCaricoRequest,
    account: Account = Depends(require_medico),
    db: Session = Depends(get_db),
):
    medico_id = account.email
    ultimo_checkin = db.query(Checkin).filter(Checkin.codice == codice).order_by(Checkin.data.desc()).first()
    if not ultimo_checkin or not ultimo_checkin.consenso_medico:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Il lavoratore non ha un consenso attivo alla condivisione con il medico.")
    pic = db.query(PresaInCarico).filter(PresaInCarico.codice == codice).first()
    if not pic:
        pic = PresaInCarico(
            codice=codice,
            stato=req.stato,
            note=req.note,
            medico_id=medico_id,
            data_presa_in_carico=datetime.utcnow(),
        )
        db.add(pic)
    else:
        pic.stato = req.stato
        if req.note is not None:
            pic.note = req.note
        pic.medico_id = medico_id
        pic.data_presa_in_carico = datetime.utcnow()

    # Traccia azione in audit log
    audit_entry = AuditLog(
        utente_id=medico_id,
        ruolo="medico",
        azione="aggiornamento_presa_in_carico",
        target_codice=codice,
        note=f"Stato impostato a '{req.stato}'",
    )
    db.add(audit_entry)
    db.commit()

    return PresaInCaricoResponse(
        codice=pic.codice,
        stato=pic.stato,
        note=pic.note,
        data_presa_in_carico=pic.data_presa_in_carico.isoformat(),
        messaggio="Presa in carico registrata con successo.",
    )

@router.get("/audit-logs", summary="Registro accessi (Audit Trail per trasparenza e GDPR)")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [{
        "id": l.id,
        "timestamp": l.timestamp.isoformat(),
        "utente_id": l.utente_id,
        "ruolo": l.ruolo,
        "azione": l.azione,
        "target_codice": l.target_codice,
        "note": l.note,
    } for l in logs]
