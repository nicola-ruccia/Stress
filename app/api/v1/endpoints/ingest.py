import os
import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.ingest import process_excel_upload
from app.schemas.schemas import IngestReportResponse
from app.api.v1.endpoints.auth import require_hr, require_medico
from app.services.mapping_archive import store_mapping, read_mapping

router = APIRouter()

@router.post("/upload-excel", response_model=IngestReportResponse, summary="Carica file Excel clinica (7 fogli)")
async def upload_excel(
    file: UploadFile = File(...),
    _account=Depends(require_hr),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato non valido: caricare un file Excel (.xlsx o .xls).",
        )

    contents = await file.read()
    try:
        report, df_mapping = process_excel_upload(contents, file.filename, db)
        # Salva CSV del mapping per il download immediato
        store_mapping(db, df_mapping.to_csv(index=False))

        return IngestReportResponse(
            timestamp=report["timestamp"],
            filename=report["filename"],
            fogli_trovati=report["fogli_trovati"],
            righe_accettate=report["righe_accettate"],
            righe_scartate=report["righe_scartate"],
            colonne_ignorate=report["colonne_ignorate"],
            errori=report["errori"],
            messaggio="Importazione completata con successo. Tabelle aggiornate e dati pseudonimizzati.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'elaborazione del file Excel: {str(e)}",
        )

@router.get("/download-mapping", summary="Scarica decodifica matricola -> codice (Riservato Medico/Admin)")
def download_mapping(_account=Depends(require_medico), db: Session = Depends(get_db)):
    mapping = read_mapping(db)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessun mapping generato recentemente. Eseguire prima un import Excel.",
        )

    stream = io.StringIO(mapping)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=decodifica_matricola_codice.csv"},
    )

@router.post("/load-demo", summary="Genera e precarica il dataset sintetico demo nel database")
def load_demo(_account=Depends(require_hr), db: Session = Depends(get_db)):
    from app.services.dataset_generator import genera_dataset_demo
    from app.models.entities import Dipendente
    if db.query(Dipendente).first():
        raise HTTPException(status_code=409, detail="Lo spazio aziendale contiene già dati. Il dataset demo non viene sovrascritto.")
    try:
        report = genera_dataset_demo(db)
        return {
            "status": "success",
            "messaggio": "Dataset sintetico clinica demo caricato con successo (150 dipendenti, 6 reparti, 24 mesi).",
            "report": report,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore generazione dataset demo: {str(e)}",
        )
