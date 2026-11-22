from typing import Optional, List
from datetime import date
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import Dipendente, Checkin, AuditLog
from app.schemas.schemas import (
    CheckinRequest,
    CheckinResponse,
    ConsensoUpdateRequest,
    LavoratoreStatoResponse,
)
from app.services.analytics import (
    load_dataframes_from_db,
    compute_all_indicators,
    get_latest_month,
)
from app.core.scoring import calcola_punteggio_sintetico
from app.core.indicators import REGISTRO

router = APIRouter()

@router.post("/accesso", summary="Verifica e accesso del lavoratore con il proprio codice")
def lavoratore_accesso(codice: str, db: Session = Depends(get_db)):
    dip = db.query(Dipendente).filter(Dipendente.codice == codice.strip()).first()
    if not dip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Codice operatore non trovato. Verificare il codice fornito dal medico o dall'amministrazione.",
        )
    return {
        "codice": dip.codice,
        "reparto": dip.reparto,
        "ruolo": dip.ruolo,
        "messaggio": "Accesso effettuato con successo.",
    }

@router.get("/mio-stato/{codice}", response_model=LavoratoreStatoResponse, summary="Visualizzazione del proprio stato e spiegazione semplice")
def get_mio_stato(codice: str, db: Session = Depends(get_db)):
    dip = db.query(Dipendente).filter(Dipendente.codice == codice.strip()).first()
    if not dip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operatore non trovato.",
        )

    data_dict = load_dataframes_from_db(db)
    target_mese = get_latest_month(data_dict)
    ind_dfs = compute_all_indicators(data_dict)

    # Raccogli indicatori personali
    ind_valori = {}
    for ind_id, ind in REGISTRO.items():
        df_ind = ind_dfs.get(ind_id)
        if df_ind is None or df_ind.empty:
            continue
        df_m = df_ind[df_ind["mese"] == target_mese] if "mese" in df_ind.columns else df_ind
        if ind.livello == "persona":
            df_c = df_m[df_m["codice"] == codice]
            if not df_c.empty:
                ind_valori[ind_id] = float(df_c["valore"].iloc[0])
        elif ind.livello == "reparto":
            df_r = df_m[df_m["reparto"] == dip.reparto]
            if not df_r.empty:
                ind_valori[ind_id] = float(df_r["valore"].iloc[0])

    score_res = calcola_punteggio_sintetico(ind_valori)

    # Spiegazione semplice e rassicurante
    if score_res["fascia"] == "alto":
        spiegazione = (
            "I tuoi indicatori di carico orario e stress segnalano un livello di affaticamento elevato. "
            "Ti consigliamo di considerare un confronto confidenziale con il medico competente."
        )
    elif score_res["fascia"] == "medio":
        spiegazione = (
            "Il tuo livello di carico lavorativo è moderato. Fai attenzione ai tempi di recupero tra i turni "
            "e all'utilizzo delle ferie."
        )
    else:
        spiegazione = (
            "I tuoi parametri di orario e benessere sono in equilibrio. Continua a monitorare periodicamente il tuo stato."
        )

    # Storico checkin
    checkins = db.query(Checkin).filter(Checkin.codice == codice).order_by(Checkin.data.desc()).all()
    storico = [{
        "data": c.data.isoformat(),
        "domanda_singola": c.domanda_singola,
        "bat12_punteggio": c.bat12_punteggio,
        "consenso_medico": c.consenso_medico,
        "richiesta_colloquio": c.richiesta_colloquio,
    } for c in checkins]

    consenso_attivo = checkins[0].consenso_medico if checkins else True

    return LavoratoreStatoResponse(
        codice=dip.codice,
        reparto=dip.reparto,
        ruolo=dip.ruolo,
        punteggio_indicativo=score_res["punteggio"],
        fascia=score_res["fascia"],
        spiegazione=spiegazione,
        consenso_medico_attivo=consenso_attivo,
        storico_checkin=storico,
    )

@router.post("/checkin", response_model=CheckinResponse, summary="Compilazione check-in mensile")
def invia_checkin(req: CheckinRequest, db: Session = Depends(get_db)):
    dip = db.query(Dipendente).filter(Dipendente.codice == req.codice.strip()).first()
    if not dip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Codice operatore non valido.",
        )

    bat12_media = None
    bat12_json = None
    if req.bat12_risposte and len(req.bat12_risposte) > 0:
        bat12_media = round(float(sum(req.bat12_risposte) / len(req.bat12_risposte)), 2)
        bat12_json = json.dumps(req.bat12_risposte)

    nuovo_chk = Checkin(
        codice=dip.codice,
        data=date.today(),
        domanda_singola=req.domanda_singola,
        bat12_punteggio=bat12_media,
        bat12_dettaglio=bat12_json,
        consenso_medico=req.consenso_medico,
        richiesta_colloquio=req.richiesta_colloquio,
    )
    db.add(nuovo_chk)

    # Traccia audit log per registrazione check-in
    audit = AuditLog(
        utente_id=dip.codice,
        ruolo="lavoratore",
        azione="compilazione_checkin",
        target_codice=dip.codice,
        note=f"Checkin registrato (consenso={req.consenso_medico}, colloquio={req.richiesta_colloquio})",
    )
    db.add(audit)
    db.commit()
    db.refresh(nuovo_chk)

    feedback = "Check-in registrato con successo. Grazie per la compilazione."
    if req.richiesta_colloquio:
        feedback += " La tua richiesta di colloquio è stata inoltrata in forma confidenziale al medico competente."

    return CheckinResponse(
        id=nuovo_chk.id,
        codice=nuovo_chk.codice,
        data=nuovo_chk.data.isoformat(),
        domanda_singola=nuovo_chk.domanda_singola,
        bat12_punteggio=nuovo_chk.bat12_punteggio,
        consenso_medico=nuovo_chk.consenso_medico,
        richiesta_colloquio=nuovo_chk.richiesta_colloquio,
        messaggio_feed=feedback,
    )

@router.put("/consenso/{codice}", summary="Aggiorna o revoca il consenso di condivisione con il medico")
def update_consenso(
    codice: str,
    req: ConsensoUpdateRequest,
    db: Session = Depends(get_db),
):
    checkins = db.query(Checkin).filter(Checkin.codice == codice.strip()).all()
    if not checkins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessun check-in trovato per questo codice.",
        )

    for chk in checkins:
        chk.consenso_medico = req.consenso_medico

    audit = AuditLog(
        utente_id=codice,
        ruolo="lavoratore",
        azione="aggiornamento_consenso",
        target_codice=codice,
        note=f"Consenso medico impostato a {req.consenso_medico}",
    )
    db.add(audit)
    db.commit()

    stato_str = "concesso" if req.consenso_medico else "revocato (i tuoi check-in non sono più visibili al medico)"
    return {
        "status": "success",
        "codice": codice,
        "consenso_medico": req.consenso_medico,
        "messaggio": f"Consenso {stato_str}.",
    }

@router.post("/richiesta-colloquio/{codice}", summary="Invia richiesta di colloquio al medico competente")
def richiesta_colloquio(codice: str, db: Session = Depends(get_db)):
    chk = db.query(Checkin).filter(Checkin.codice == codice.strip()).order_by(Checkin.data.desc()).first()
    if chk:
        chk.richiesta_colloquio = True
        chk.consenso_medico = True  # La richiesta implica la possibilità per il medico di contattarlo
    else:
        # Se non ha mai fatto checkin, crea una registrazione ad hoc
        nuovo = Checkin(
            codice=codice,
            data=date.today(),
            domanda_singola=3,
            consenso_medico=True,
            richiesta_colloquio=True,
        )
        db.add(nuovo)

    audit = AuditLog(
        utente_id=codice,
        ruolo="lavoratore",
        azione="richiesta_colloquio_medico",
        target_codice=codice,
        note="Richiesta colloquio inoltrata",
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "codice": codice,
        "messaggio": "Richiesta di colloquio registrata. Il medico competente visualizzerà la tua disponibilità.",
    }
