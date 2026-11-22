# Account demo per i giudici

Questi account sono esclusivamente dimostrativi. Usano dati sintetici e condividono la stessa azienda demo. Non riutilizzare le password per account reali.

| Vista | Email | Password |
|---|---|---|
| HR | `giudice.hr@demo.semalia.it` | `SemaliaHR2026!` |
| Medico | `giudice.medico@demo.semalia.it` | `SemaliaMedico2026!` |
| Dipendente | `giudice.dipendente@demo.semalia.it` | `SemaliaStaff2026!` |

## Preparazione del database

Gli account vanno creati una volta nel database effettivamente usato dalla demo. Il comando aggiunge il dataset sintetico solo se il database tenant demo è vuoto; non cancella dati aziendali già presenti. Il codice dipendente è associato automaticamente al primo lavoratore sintetico.

1. Configura `DATABASE_URL`, `SECRET_KEY` e `PSEUDO_KEY` per il database desiderato. Per Vercel, usa l'URL PostgreSQL della produzione e le stesse chiavi configurate nel progetto.
2. Dalla cartella principale del repository esegui il comando per l'ambiente scelto. Per il database locale:

   ```powershell
   python scripts/seed_judge_accounts.py --create-demo
   ```

   Per Vercel, installa/autentica la CLI (`npm install --global vercel`, `vercel login`) e collega la cartella al progetto (`vercel link`). Scarica le variabili di produzione in un file separato, poi esegui il seed:

   ```powershell
   vercel env pull .env.production.local --environment=production
   python scripts/seed_judge_accounts.py --create-demo --env-file .env.production.local
   ```

   Il file deve contenere `DATABASE_URL` con la connessione PostgreSQL di produzione, oltre alle stesse `SECRET_KEY` e `PSEUDO_KEY` configurate su Vercel. Se l'integrazione database espone la connessione con un altro nome, aggiungi `DATABASE_URL` nelle variabili del progetto.

3. Ridistribuisci il progetto se hai aggiornato variabili o codice su Vercel.

Il comando è esplicito e non viene eseguito automaticamente all'avvio. Ripeterlo riattiva e reimposta le password dei tre account demo.
