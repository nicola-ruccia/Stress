from fastapi import APIRouter, HTTPException, status
from app.schemas.schemas import DemoLoginRequest, DemoLoginResponse

router = APIRouter()

@router.post("/demo-login", response_model=DemoLoginResponse, summary="Login simulato rapido per demo/PoC")
def demo_login(req: DemoLoginRequest):
    ruoli_validi = {"hr", "medico", "lavoratore", "admin"}
    ruolo_clean = req.ruolo.lower().strip()

    if ruolo_clean not in ruoli_validi:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ruolo non valido. Ruoli supportati: {list(ruoli_validi)}",
        )

    if ruolo_clean == "lavoratore" and not req.codice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Il codice pseudonimo è obbligatorio per l'accesso del lavoratore.",
        )

    # Token fittizio per demo (in MVP sostituibile con JWT reale)
    token = f"demo_token_{ruolo_clean}_{req.codice or 'user'}"

    return DemoLoginResponse(
        token=token,
        ruolo=ruolo_clean,
        codice=req.codice,
        messaggio=f"Accesso consentito con ruolo '{ruolo_clean}'",
    )
