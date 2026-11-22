import os
import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.ingest import process_excel_upload
from app.schemas.schemas import IngestReportResponse

router = APIRouter()

# Conserva in memoria l'ultimo mapping generato (da distribuire esclusivamente al medico/admin)
LAST_MAPPING_CSV = ""

@router.post("/upload-excel", response_model=IngestReportResponse, summary="Carica file Excel clinica (7 fogli)")
async def upload_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    global LAST_MAPPING_CSV
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato non valido: caricare un file Excel (.xlsx o .xls).",
        )

    contents = await file.read()
    try:
        report, df_mapping = process_excel_upload(contents, file.filename, db)
        # Salva CSV del mapping per il download immediato
        LAST_MAPPING_CSV = df_mapping.to_csv(index=False)

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
def download_mapping():
    global LAST_MAPPING_CSV
    if not LAST_MAPPING_CSV:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessun mapping generato recentemente. Eseguire prima un import Excel.",
        )

    stream = io.StringIO(LAST_MAPPING_CSV)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=decodifica_matricola_codice.csv"},
    )

@router.post("/load-demo", summary="Genera e precarica il dataset sintetico demo nel database")
def load_demo(db: Session = Depends(get_db)):
    from app.services.dataset_generator import genera_dataset_demo
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
