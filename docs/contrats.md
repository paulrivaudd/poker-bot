# Contrats

Toute modification passe par une PR validée par les 4 membres.

## Cartes
Chaîne de 2 caractères : rang `23456789TJQKA` + couleur `shdc`.
Exemples : `"As"`, `"Td"`, `"7h"`.

## Moteur (`backend/engine`)
```python
evaluate(cards: list[str]) -> int
# 5 à 7 cartes, plus grand = meilleure main

equity(hand: list[str], board: list[str], n_opponents: int, n_sims: int = 10000) -> dict
# {"win": float, "tie": float, "lose": float}, somme = 1
```

## Décision (`backend/decision`)
```python
analyze(equity: float, pot: float, to_call: float) -> dict
# {"pot_odds": float, "ev": {"fold": float, "call": float}, "recommendation": "fold" | "call"}
```
- `pot_odds = to_call / (pot + to_call)`
- `EV(fold) = 0`
- `EV(call) = equity * (pot + to_call) - to_call`
- `call` si `equity > pot_odds`, sinon `fold`
- `equity` = `win + tie / 2`

## API
### `POST /api/analyze`
Entrée :
```json
{"hand": ["As","Kd"], "board": ["7h","8c","2s"], "n_opponents": 1,
 "pot": 100, "to_call": 20, "n_sims": 10000}
```
Sortie `200` :
```json
{"equity": 0.62, "win": 0.60, "tie": 0.04, "pot_odds": 0.167,
 "ev": {"fold": 0, "call": 54.4}, "recommendation": "call"}
```
Erreur `400` : `{"error": "message"}`
- carte invalide, doublon entre main et board
- main ≠ 2 cartes, board ∉ {0, 3, 4, 5} cartes
- `n_opponents` ∉ [1, 9], `pot` < 0, `to_call` < 0

### `GET /api/health`
`{"status": "ok"}`
