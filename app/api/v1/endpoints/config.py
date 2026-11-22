from fastapi import APIRouter
from app.core.config import soglie_config, settings

router = APIRouter()

@router.get("/soglie", summary="Restituisce la configurazione attiva di soglie, fasce e azioni suggerite")
def get_soglie_config():
    return {
        "k_min": settings.K_MIN,
        "retention_mesi": settings.RETENTION_MESI,
        "avvisi_orario_hr": settings.AVVISI_ORARIO_HR,
        "costo_turnover_default": settings.COSTO_TURNOVER_DEFAULT,
        "fasce": soglie_config.get("fasce", {"basso": 34, "alto": 66}),
        "indicatori": soglie_config.get("indicatori", {}),
        "azioni_suggerite": soglie_config.get("azioni_suggerite", {}),
    }
