import hashlib
import hmac
from typing import Optional, Set
from app.core.config import settings

# Whitelist rigida dei campi ammessi per ciascuno dei 7 fogli Excel
ALLOWED_EXCEL_FIELDS = {
    "dipendenti": {
        "matricola",
        "reparto",
        "ruolo",
        "data_assunzione",
        "data_cessazione",
        "tipo_cessazione",
    },
    "turni": {
        "matricola",
        "reparto",
        "inizio",
        "fine",
    },
    "assenze": {
        "matricola",
        "tipo",
        "data_inizio",
        "data_fine",
    },
    "ore_mese": {
        "matricola",
        "mese",
        "ore_straordinario",
        "ferie_residue_giorni",
    },
    "eventi_hr": {
        "matricola",
        "data",
        "tipo",
    },
    "aggressioni": {
        "reparto",
        "data",
    },
    "occupazione": {
        "reparto",
        "data",
        "pazienti_presenti",
    },
}

def pseudonimize_matricola(matricola: str, key: Optional[str] = None) -> str:
    """
    Calcola il codice pseudonimo: HMAC-SHA256(matricola, PSEUDO_KEY), troncato a 10 caratteri.
    Garantisce determinismo all'interno dell'istanza ma irreversibilità per chi non ha la chiave.
    La matricola non viene MAI salvata nel database.
    """
    secret = (key or settings.PSEUDO_KEY).encode("utf-8")
    raw = str(matricola).strip().encode("utf-8")
    h = hmac.new(secret, raw, hashlib.sha256).hexdigest()
    return h[:10]

def is_k_min_satisfied(count: int, k_min: Optional[int] = None) -> bool:
    """
    Regola k-anonymity: un dato aggregato si mostra solo se riguarda almeno K_MIN persone.
    """
    min_val = k_min if k_min is not None else settings.K_MIN
    return count >= min_val

def puo_vedere(indicatore_id: str, ruolo: str, livello: str = "reparto") -> bool:
    """
    Verifica se il ruolo ha diritto legale/organizzativo di visualizzare l'indicatore.
    Ruoli ammessi: 'hr', 'medico', 'lavoratore', 'admin'.
    Regole ferree:
      - HR: NON vede MAI assenze individuali, checkin individuali o BAT-12 individuali.
      - Medico: vede tutto sia a livello reparto che individuale (check-in solo con consenso).
      - Lavoratore: vede solo la propria scheda/check-in.
    """
    r = ruolo.lower()
    if r == "admin":
        return True

    # Indicatori strettamente individuali e sanitari
    if indicatore_id in {"checkin", "bat12", "malattia_brevi"}:
        if livello == "persona":
            if r == "hr":
                return False
            if r in {"medico", "lavoratore"}:
                return True
        elif livello == "reparto":
            # Per HR il check-in è visibile solo come percentuale aggregata se ci sono almeno K_MIN risposte
            return True

    if r == "hr":
        if livello == "persona":
            # HR vede il dato del singolo solo per indicatori di orario se l'opzione è attiva
            if settings.AVVISI_ORARIO_HR and indicatore_id in {"rientri_rapidi", "turni_lunghi"}:
                return True
            return False
        return True

    if r == "medico":
        return True

    if r == "lavoratore":
        return indicatore_id in {"checkin", "bat12"}

    return False
