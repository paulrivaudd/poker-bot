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
# {"win": float, "tie": float, "lose": float, "share": float}
# win + tie + lose = 1 ; share = part moyenne du pot (partages à k joueurs comptés 1/k)
```

## Décision (`backend/decision`)
```python
analyze(equity: float, pot: float, to_call: float) -> dict
# {"pot_odds": float, "ev": {"fold": float, "call": float}, "recommendation": "fold" | "call" | "check"}
```
- `pot_odds = to_call / (pot + to_call)`
- `EV(fold) = 0`
- `EV(call) = equity * (pot + to_call) - to_call`
- `check` si `to_call == 0`, sinon `call` si `equity > pot_odds`, sinon `fold`
- `equity` = `share` renvoyé par le moteur

## API
### `POST /api/analyze`
Entrée :
```json
{"hand": ["As","Kd"], "board": ["7h","8c","2s"], "n_opponents": 1,
 "pot": 100, "to_call": 20, "n_sims": 10000}
```
Sortie `200` :
```json
{"equity": 0.62, "win": 0.60, "tie": 0.04, "lose": 0.36,
 "hand_name": "Carte haute", "pot_odds": 0.167,
 "ev": {"fold": 0, "call": 54.4}, "recommendation": "call"}
```
Erreur `400` : `{"error": "message"}`
- carte invalide, doublon entre main et board
- main ≠ 2 cartes, board ∉ {0, 3, 4, 5} cartes
- `n_opponents` ∉ [1, 9], `pot` < 0, `to_call` < 0

`hand_name` vaut `null` préflop.

### `GET /api/health`
`{"status": "ok"}`
