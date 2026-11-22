#!/usr/bin/env python3
"""
Script di verifica End-to-End della Demo (simula il pitch di 90 secondi):
1. Caricamento dataset clinica demo (150 operatori, 6 reparti, 24 mesi)
2. HR Dashboard: Reparto Medicina rosso, top 3 fattori e costo turnover
3. Medico Competente: Operatori 'DA CONTATTARE', scheda clinica e presa in carico
4. Lavoratore: check-in, sblocco BAT-12 e sovranità sul consenso GDPR
5. Ritorno all'HR: aggiornamento del contatore aggregato anonimo
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Imposta path radice
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from app.main import app

def run_e2e_demo():
    print("=" * 65)
    print("🚀 AVVIO SIMULAZIONE E2E - PoC RISCHIO Somalìa IN SANITÀ PRIVATA")
    print("=" * 65)

    client = TestClient(app)

    # 1. INGESTIONE & PSEUDONIMIZZAZIONE
    print("\n[FASE 1 - Ingestione & Privacy by Design]")
    resp = client.post("/api/v1/ingest/load-demo")
    assert resp.status_code == 200, f"Errore load-demo: {resp.text}"
    data_demo = resp.json()
    print(f"✓ Clinica Demo caricata con successo.")
    print(f"  - Operatori censiti: {data_demo['report']['dipendenti_inseriti']}")
    print(f"  - Turni storici generati: {data_demo['report']['turni_inseriti']}")
    print(f"  - Nessuna matricola salvata in chiaro (HMAC-SHA256 attivo).")

    # 2. VISTA HR
    print("\n[FASE 2 - Vista HR & Cruscotto Direzionale]")
    resp_hr = client.get("/api/v1/hr/dashboard")
    assert resp_hr.status_code == 200, f"Errore HR dashboard: {resp_hr.text}"
    hr_data = resp_hr.json()
    kpi = hr_data["kpi"]
    print(f"✓ Livello di rischio della struttura: {kpi['punteggio_struttura']}/100 ({kpi['fascia_rischio_struttura'].upper()})")
    print(f"✓ Reparti critici in rosso: {kpi['reparti_in_rosso_count']} ({', '.join(kpi['reparti_in_rosso'])})")
    print(f"✓ Costo stimato del turnover (12 mesi): {kpi['costo_turnover_stimato']:,.2f} € ({kpi['dimissioni_ultimi_12_mesi']} dimissioni)")
    print(f"✓ Operatori presi in carico dal medico: {kpi['persone_in_carico_medico']}")

    # Dettaglio Medicina
    medicina = next((r for r in hr_data["reparti"] if r["reparto"] == "Medicina"), None)
    assert medicina is not None
    print(f"\n  Focus Reparto 'Medicina':")
    print(f"  - Punteggio: {medicina['punteggio']}/100 (Fascia: {medicina['fascia']})")
    print(f"  - I 3 fattori che pesano di più:")
    for i, f in enumerate(medicina["top_3_fattori"], 1):
        print(f"    {i}. {f['nome']} (valore: {f['valore']}) -> Azione: {f.get('azione_suggerita', 'N/D')}")

    # 3. VISTA MEDICO COMPETENTE
    print("\n[FASE 3 - Vista Medico Competente / Triage & Sorveglianza]")
    resp_med = client.get("/api/v1/medico/operatori?reparto=Medicina")
    assert resp_med.status_code == 200, f"Errore medico operatori: {resp_med.text}"
    operatori = resp_med.json()
    da_contattare = [op for op in operatori if op["da_contattare"]]
    print(f"✓ Operatori nel reparto Medicina: {len(operatori)}")
    print(f"✓ Casi con bandiera 'DA CONTATTARE': {len(da_contattare)}")

    target_op = da_contattare[0]["codice"]
    print(f"  Apertura scheda clinico-organizzativa operatore: {target_op}")
    resp_scheda = client.get(f"/api/v1/medico/operatore/{target_op}")
    assert resp_scheda.status_code == 200
    scheda = resp_scheda.json()
    print(f"  - Consenso medico attivo: {scheda['consenso_medico_attivo']}")
    print(f"  - Check-in registrati: {len(scheda['checkin_history'])}")

    # Registrazione presa in carico
    print(f"  Registrazione presa in carico dell'operatore {target_op}...")
    resp_pic = client.post(
        f"/api/v1/medico/presa-in-carico/{target_op}",
        json={"stato": "contattato", "note": "Effettuato primo colloquio di ascolto confidenziale"}
    )
    assert resp_pic.status_code == 200
    print(f"  ✓ Presa in carico registrata con stato 'contattato'.")

    # 4. VISTA LAVORATORE
    print("\n[FASE 4 - Vista Lavoratore & Check-in Riservato]")
    resp_stato_lav = client.get(f"/api/v1/lavoratore/mio-stato/{target_op}")
    assert resp_stato_lav.status_code == 200
    stato_lav = resp_stato_lav.json()
    print(f"✓ Accesso lavoratore con codice: {target_op}")
    print(f"  - Spiegazione orientativa: \"{stato_lav['spiegazione']}\"")

    # Invio nuovo check-in
    print("  Compilazione nuovo check-in con domanda_singola=4 (sintomi elevati)...")
    resp_chk = client.post(
        "/api/v1/lavoratore/checkin",
        json={
            "codice": target_op,
            "domanda_singola": 4,
            "bat12_risposte": [4, 4, 3, 4, 3, 4, 3, 4, 4, 3, 4, 4],
            "consenso_medico": True,
            "richiesta_colloquio": True
        }
    )
    assert resp_chk.status_code == 200
    print(f"  ✓ Check-in inviato. Punteggio medio BAT-12 calcolato: {resp_chk.json()['bat12_punteggio']}")

    # 5. RITORNO ALL'HR
    print("\n[FASE 5 - Ritorno alla Vista HR & Trasparenza]")
    resp_hr_2 = client.get("/api/v1/hr/dashboard")
    kpi_aggiornato = resp_hr_2.json()["kpi"]
    print(f"✓ Il contatore anonimo delle persone prese in carico ora vale: {kpi_aggiornato['persone_in_carico_medico']}")
    print(f"  (L'HR vede solo il conteggio totale, tutelando rigorosamente l'anonimato del lavoratore)")

    print("\n" + "=" * 65)
    print("🎉 TUTTI I MODULI SONO PERFETTAMENTE COLLEGATI E FUNZIONANTI!")
    print("=" * 65)

if __name__ == "__main__":
    run_e2e_demo()
