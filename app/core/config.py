import os
from pathlib import Path
from typing import Any, Dict, List
import yaml
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Burnout Risk PoC Backend"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    PSEUDO_KEY: str = "chiave_segreta_hmac_sanita_privata_demo"
    DATABASE_URL: str = "sqlite:///./burnout.db"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    K_MIN: int = 6
    RETENTION_MESI: int = 24
    AVVISI_ORARIO_HR: bool = False
    COSTO_TURNOVER_DEFAULT: float = 45000.0

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

def load_soglie_config() -> Dict[str, Any]:
    yaml_path = BASE_DIR / "config" / "soglie.yaml"
    if not yaml_path.exists():
        return {}
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

soglie_config = load_soglie_config()
