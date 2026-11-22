from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    ingest,
    hr,
    medico,
    lavoratore,
    config,
    compat,
)

api_router = APIRouter()

api_router.include_router(compat.router, tags=["Stressa Frontend Compatibility"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticazione / Demo"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestione Dati / Excel"])
api_router.include_router(hr.router, prefix="/hr", tags=["Vista HR"])
api_router.include_router(medico.router, prefix="/medico", tags=["Vista Medico Competente / Psicologo"])
api_router.include_router(lavoratore.router, prefix="/lavoratore", tags=["Vista Lavoratore"])
api_router.include_router(config.router, prefix="/config", tags=["Configurazione & Soglie"])
