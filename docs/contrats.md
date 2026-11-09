# Contrats

Toute modification passe par une PR validée par les 4 membres.

## Cartes
Chaîne de 2 caractères : rang `23456789TJQKA` + couleur `shdc`.
Exemples : `"As"`, `"Td"`, `"7h"`.

## Moteur (`backend/engine`)
```python
evaluate(cards: list[str]) -> int
# 5 à 7 cartes, plus grand = meilleure main

evaluate(cards) -> int          # catégorie * 16^5 + 5 kickers (4 bits chacun)
hand_name(cards) -> str         # "Paire", "Full", ...

equity(hand: list[str], board: list[str], n_opponents: int,
       n_sims: int = 10000, seed: int | None = None) -> dict
# {"win", "tie", "lose", "share", "share_ci"}  (share_ci = demi-largeur IC 95 %)
# win + tie + lose = 1 ; share = part moyenne du pot (partages à k joueurs comptés 1/k)
```

## Décision (`backend/decision`)
```python
analyze(equity, pot, to_call, raise_size=None, fold_equity=0.3) -> dict
# {"pot_odds", "ev": {"fold", "call"|"check", "raise"}, "raise_size", "recommendation"}
```
Conventions : `pot` inclut la mise adverse, `to_call` = montant à ajouter pour suivre,
`raise_size` = montant total ajouté en relançant (défaut : relance taille du pot = `to_call + pot + to_call`).

- `pot_odds = to_call / (pot + to_call)`
- `EV(fold) = 0`
- `EV(call) = equity * (pot + to_call) - to_call` (s'appelle `check` si `to_call == 0`)
- `EV(raise) = f * pot + (1 - f) * (equity * (pot + 2*raise_size - to_call) - raise_size)`, `f` = fold equity
- Recommandation = action d'EV maximale (jamais `fold` si `check` est gratuit)
- Hypothèses : pas de sur-relance, équité inchangée quand l'adversaire paie
- `equity` = `share` renvoyé par le moteur

## API
### `POST /api/analyze`
Entrée :
```json
{"hand": ["As","Kd"], "board": ["7h","8c","2s"], "n_opponents": 1,
 "pot": 100, "to_call": 20, "n_sims": 10000,
 "raise_size": null, "fold_equity": 0.3}
```
Sortie `200` :
```json
{"equity": 0.62, "equity_ci": 0.009, "win": 0.60, "tie": 0.04, "lose": 0.36,
 "hand_name": "Carte haute", "pot_odds": 0.167,
 "ev": {"fold": 0, "call": 54.4, "raise": 61.2}, "raise_size": 140,
 "recommendation": "raise"}
```
Erreur `400` : `{"error": "message"}`
- carte invalide, doublon entre main et board
- main ≠ 2 cartes, board ∉ {0, 3, 4, 5} cartes
- `n_opponents` ∉ [1, 9], `pot` < 0, `to_call` < 0
- `fold_equity` ∉ [0, 1], `raise_size` ≤ `to_call`

`hand_name` vaut `null` préflop.

### `GET /api/health`
`{"status": "ok"}`
