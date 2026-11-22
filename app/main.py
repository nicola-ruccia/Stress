from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend API per il monitoraggio del rischio burnout nella sanità privata.\n\n"
        "Caratteristiche architetturali principali:\n"
        "- **Privacy by Design**: Pseudonimizzazione HMAC all'import, k-anonymity (K_MIN=6), audit trail accessi.\n"
        "- **Spiegabilità scientifica**: 13 indicatori oggettivi (INAIL, BAT-12, turnistica, assenze) con semafori e top 3 fattori.\n"
        "- **Separazione dei ruoli**: Endpoint dedicati per Amministrazione/Ingestione, HR, Medico Competente e Lavoratore."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurazione CORS per abilitare il frontend (React, Next.js, Vite, Vue, ecc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health", tags=["Healthcheck"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "k_min": settings.K_MIN,
        "docs_url": "/docs",
    }

app.include_router(api_router, prefix=settings.API_V1_STR)

BASE_DIR = Path(__file__).resolve().parent.parent

@app.get("/", include_in_schema=False)
def serve_root():
    colleague_html = BASE_DIR / "stressa_piattaforma_aziendale_stress_burnout.html"
    if colleague_html.exists():
        return FileResponse(str(colleague_html))
    return {"message": "Stressa Burnout Backend Running. See /docs for API."}

@app.get("/video-demo", include_in_schema=False)
def serve_video_demo():
    video_html = BASE_DIR / "docs" / "DEMO_PRESENTATION_VIDEO.html"
    if video_html.exists():
        return FileResponse(str(video_html))
    return {"message": "Video demo not found"}



