# Poker Bot — Aide à la décision Texas Hold'em

Application web : back-end Flask (API REST) + front-end séparé.
Deux modes au lancement :
- **TRICHE** : on entre sa main (et le board), l'appli calcule l'équité et recommande fold / call / raise
  (cotes implicites, multiway, fold equity par adversaire).
- **JEU** : vraie partie de No-Limit Hold'em (2 à 10 joueurs), en solo contre des bots qui décident avec
  notre moteur (Monte Carlo + module décision), ou en multijoueur local sur le même ordinateur.

## Lancer le projet

```bash
# Back-end
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows : voir plus bas
pip install -r requirements.txt
python app.py                    # ouvrir http://localhost:5000

# Tests
pytest
```

Windows PowerShell : `.venv\Scripts\Activate.ps1` (si bloqué : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`).

Flask sert aussi le front-end : une seule commande suffit.
Pour développer le front seul : `cd frontend; python -m http.server 8000`.

Dans `frontend/app.js`, `USE_MOCK = true` utilise `mock/analyze.json` sans back-end.

## Organisation

- Contrats (cartes, signatures, API) : voir [`docs/contrats.md`](docs/contrats.md)
- Un dossier par pôle : `backend/engine` (A), `backend/decision` (B), `backend/api` + `backend/tests` (C), `frontend` (D)
- Chacun ne modifie que son dossier ; `docs/contrats.md` et `backend/app.py` sont partagés (PR relue obligatoire)
- `main` doit toujours tourner de bout en bout et la CI être verte
