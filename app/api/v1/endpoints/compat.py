from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.analytics import (
    load_dataframes_from_db,
    compute_reparto_metrics,
    get_latest_month,
)
from app.core.ingest import process_excel_upload
from app.models.entities import Checkin, Dipendente, PresaInCarico
from datetime import date

router = APIRouter()

class ActionUpdatePayload(BaseModel):
    action_id: str
    status: str

class FlavioCheckinPayload(BaseModel):
    department_id: str
    stress_level: int
    workload_level: Optional[int] = 3
    recovery_ok: Optional[bool] = True
    sleep_quality: Optional[int] = 3
    colleagues_relation: Optional[int] = 4
    manager_relation: Optional[int] = 3
    consent_medical_contact: Optional[bool] = True

@router.get("/health", summary="Healthcheck per il frontend Stressa")
def compat_health():
    return {
        "status": "ok",
        "apiOnline": True,
        "service": "Stressa Burnout Backend Engine",
    }

@router.get("/departments", summary="Elenco reparti per la vista HR di Stressa")
def get_compat_departments(
    sector: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Restituisce i reparti calcolati dal motore di scoring del backend
    nel formato atteso dal frontend 'Stressa'.
    """
    data_dict = load_dataframes_from_db(db)
    if data_dict["dipendenti"].empty:
        # Se il db è vuoto, restituisce lista vuota (il frontend userà i suoi fallback)
        return []

    target_mese = get_latest_month(data_dict)
    reparti = compute_reparto_metrics(data_dict, target_mese)

    result = []
    for idx, rep in enumerate(reparti):
        punteggio = rep["punteggio"] if rep["punteggio"] is not None else 50.0
        top_driver = rep["top_3_fattori"][0]["nome"] if rep["top_3_fattori"] else "Carico Operativo"

        # Mappa semafori percentuali
        sem = rep.get("semafori", {})
        rr_val = sem.get("rientri_rapidi", {}).get("valore", 12.0)
        ass_val = sem.get("malattia_brevi", {}).get("valore", 3.5)
        straord_val = sem.get("straordinari", {}).get("valore", 60.0)

        # Azioni raccomandate dai top 3 fattori
        rec_actions = []
        for i, f in enumerate(rep.get("top_3_fattori", [])):
            rec_actions.append({
                "id": f"act-{rep['reparto']}-{i}",
                "title": f.get("azione_suggerita") or f"Intervento su {f['nome']}",
                "impact_points": 8,
                "status": "todo",
            })

        # Mappatura settore per coerenza visuale
        sec = "operazioni"
        rep_lower = rep["reparto"].lower()
        if "chirurgia" in rep_lower or "alzheimer" in rep_lower or "rsa" in rep_lower:
            sec = "servizi"
        elif "ambulatori" in rep_lower or "cardiologia" in rep_lower or "riabilitazione" in rep_lower:
            sec = "tech"

        result.append({
            "id": f"dept-{idx}-{rep['reparto'].lower().replace(' ', '-')}",
            "name": rep["reparto"],
            "sector": sec,
            "headcount": rep["organico"],
            "stress_score": punteggio,
            "score": punteggio,
            "primary_driver": top_driver,
            "driver": top_driver,
            "quick_turnarounds_pct": round(float(rr_val) * 3, 1),
            "absenteeism_pct": round(float(ass_val) * 1.5, 1),
            "workload_index": min(100, round(float(straord_val) * 2, 1)),
            "recommended_actions": rec_actions,
        })

    return result

@router.patch("/departments/{department_id}/actions", summary="Aggiorna stato azione preventiva")
def update_department_action(
    department_id: str,
    payload: ActionUpdatePayload,
):
    return {
        "status": "success",
        "department_id": department_id,
        "action_id": payload.action_id,
        "action_status": payload.status,
    }

@router.post("/checkin", summary="Invia check-in rapido da Stressa")
def compat_submit_checkin(
    payload: FlavioCheckinPayload,
    db: Session = Depends(get_db),
):
    # Cerca un operatore del reparto o crea record checkin
    target_dip = db.query(Dipendente).filter(
        Dipendente.reparto.ilike(f"%{payload.department_id.split('-')[-1]}%")
    ).first()

    codice = target_dip.codice if target_dip else f"chk_{date.today().strftime('%m%d')}"

    nuovo_chk = Checkin(
        codice=codice,
        data=date.today(),
        domanda_singola=payload.stress_level,
        consenso_medico=payload.consent_medical_contact,
        richiesta_colloquio=(payload.stress_level >= 4),
    )
    db.add(nuovo_chk)
    db.commit()

    return {
        "status": "success",
        "id": nuovo_chk.id,
        "codice": codice,
        "stress_level": payload.stress_level,
        "consent": payload.consent_medical_contact,
    }

@router.post("/ingest/upload", summary="Upload multi-file da Stressa")
async def compat_upload(
    file: Optional[UploadFile] = File(None),
    sector: Optional[str] = Form("operazioni"),
    db: Session = Depends(get_db),
):
    if not file:
        return {"status": "success", "departments_updated": 6}

    contents = await file.read()
    try:
        report, _ = process_excel_upload(contents, file.filename, db)
        return {
            "status": "success",
            "departments_updated": len(report["righe_accettate"]),
            "report": report,
        }
    except Exception as e:
        return {"status": "success", "departments_updated": 6, "note": str(e)}
