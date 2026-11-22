#!/usr/bin/env python3
"""
Script per la generazione autonoma dei dataset sintetici per la demo e per il modello Excel vuoto.
Esegui con: python data/genera_dataset.py
"""
import sys
from pathlib import Path

# Aggiungi root directory al pythonpath
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from app.services.dataset_generator import esporta_file_demo

if __name__ == "__main__":
    print("Generazione dataset sintetico clinica demo in corso...")
    result = esporta_file_demo()
    print("Generazione completata con successo:")
    for k, v in result.items():
        print(f" - {k}: {v}")
