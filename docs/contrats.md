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
analyze(equity, pot, to_call, raise_size=None, fold_equity=0.3,
        n_opponents=1, players_behind=0, effective_stack=None, implied_fraction=0.5,
        hand=None, board=None, equity_curve=None) -> dict
# {"pot_odds", "expected_pot", "ev": {"fold", "call"|"check", "raise"},
#  "ev_call_direct", "ev_call_implied", "p_set", "p_all_fold", "raise_size", "recommendation"}
```
Conventions : `pot` = ce qu'il y a au milieu, `to_call` = montant à ajouter pour suivre,
`raise_size` = montant total ajouté en relançant (défaut : relance taille du pot = `to_call + pot + to_call`).
`f` = `fold_equity` = probabilité qu'**un** adversaire se couche (indépendamment des autres),
`n` = `n_opponents`, `b` = `players_behind` (adversaires qui parlent encore après nous, `0 ≤ b ≤ n`).

- `pot_odds = to_call / (pot + to_call)` (cote classique, affichée)
- `expected_pot = pot + to_call + b * (1 - f) * to_call` (multiway : les joueurs derrière paient avec proba 1 − f)
- `EV(fold) = 0`
- `EV(call) direct = equity * expected_pot - to_call` (s'appelle `check` si `to_call == 0`)
- Cotes implicites, si paire servie sans brelan et `effective_stack` fourni :
  `p_set` = P(brelan ou mieux à la prochaine rue) = `1 - C(48,3)/C(50,3) ≈ 11,8 %` préflop, `2/47` au flop, `2/46` au turn ;
  `EV(call) implicite = p_set * (expected_pot + implied_fraction * (effective_stack - to_call)) - to_call`
  (on se couche si on rate, on récupère une part du tapis effectif si on touche).
  `ev[call] = max(direct, implicite)`.
- `EV(raise) = f^n * pot + Σ_{m=1..n} C(n,m) (1-f)^m f^(n-m) * (eq_m * (pot + raise_size + m * c) - raise_size)`
  avec `c = raise_size - to_call * (1 - b/n)` (mise moyenne d'un payeur) et `eq_m = equity_curve[m-1]`
  (équité contre m adversaires ; à défaut `equity`). `p_all_fold = f^n`.
- Recommandation = action d'EV maximale (jamais `fold` si `check` est gratuit)
- Hypothèses : pas de sur-relance ; mains adverses aléatoires ; on gagne toujours quand on touche le brelan.
- `equity` = `share` renvoyé par le moteur ; `equity_curve` = `engine.equity_curve(hand, board, n)`

## Partie (`backend/game`, mode JEU)
`Game(players=[(nom, est_bot)], stack, small_blind, big_blind)` : NLHE complet (blinds, relance minimum,
tapis, pots annexes, showdown). `act(action, amount)` avec `action ∈ {fold, check, call, raise, allin}`,
`amount` = montant **total** misé sur la rue (« relance à »). `view(viewer)` = état JSON (seules les cartes
de `viewer` et celles montrées au showdown sont visibles). Les bots (`game/bot.py`) décident avec
`equity_curve` + `analyze`.

## API
### `POST /api/analyze`
Entrée :
```json
{"hand": ["As","Kd"], "board": ["7h","8c","2s"], "n_opponents": 1,
 "pot": 100, "to_call": 20, "n_sims": 10000,
 "raise_size": null, "fold_equity": 0.3,
 "players_behind": 0, "effective_stack": null, "implied_fraction": 0.5}
```
Sortie `200` :
```json
{"equity": 0.62, "equity_ci": 0.009, "win": 0.60, "tie": 0.04, "lose": 0.36,
 "hand_name": "Carte haute", "pot_odds": 0.167,
 "expected_pot": 120, "ev": {"fold": 0, "call": 54.4, "raise": 61.2},
 "ev_call_direct": 54.4, "ev_call_implied": null, "p_set": null, "p_all_fold": 0.3,
 "raise_size": 140, "recommendation": "raise"}
```
Erreur `400` : `{"error": "message"}`
- carte invalide, doublon entre main et board
- main ≠ 2 cartes, board ∉ {0, 3, 4, 5} cartes
- `n_opponents` ∉ [1, 9], `pot` < 0, `to_call` < 0
- `fold_equity` ∉ [0, 1], `raise_size` ≤ `to_call`
- `players_behind` ∉ [0, n_opponents], `effective_stack` < 0, `implied_fraction` ∉ [0, 1]

`hand_name` vaut `null` préflop.

### `GET /api/health`
`{"status": "ok"}`

### Mode JEU : `/api/game`
Toutes les routes acceptent `?viewer=<index>` (joueur dont on veut voir les cartes).
- `POST /api/game/new` `{"players": [{"name": "Moi"}, {"name": "Bot 1", "bot": true}], "stack": 1000, "small_blind": 5, "big_blind": 10}` → état, première main distribuée
- `GET /api/game/<id>` → état
- `POST /api/game/<id>/action` `{"action": "raise", "amount": 60}` → joue pour l'humain dont c'est le tour
- `POST /api/game/<id>/bot` → fait jouer **une** action à l'ordinateur dont c'est le tour
- `POST /api/game/<id>/next` → main suivante

État : `{"id", "hand_no", "street", "board", "pot", "button", "current", "current_bet", "sb", "bb",
"players": [{"name", "bot", "stack", "bet", "folded", "all_in", "out", "n_cards", "hole"}],
"legal": {"fold", "check", "call", "call_amount", "raise": {"min", "max"} | null},
"hand_over", "results": [{"name", "amount", "hand_name"}], "game_over", "winner", "log"}`.
Erreurs : `400` action illégale, `404` partie inconnue.
