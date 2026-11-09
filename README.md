# Poker Bot — Aide à la décision Texas Hold'em

Application web : back-end Flask (API REST) + front-end séparé.
MVP : Texas Hold'em No-Limit, heads-up.

## Contrats (à respecter par tous)

Toute modification passe par une PR validée par les 4 membres.

### Cartes
Chaîne de 2 caractères : rang `23456789TJQKA` + couleur `shdc`.
Exemples : `"As"`, `"Td"`, `"7h"`.

### Moteur (Python)
```python
evaluate(cards: list[str]) -> int
# 5 à 7 cartes, plus grand = meilleur

equity(hand, board, n_opponents, n_sims=10000) -> dict
# {"win": float, "tie": float, "lose": float}
```

### API
```
POST /api/analyze
```
Entrée :
```json
{
  "hand": ["As", "Kd"],
  "board": ["7h", "8c", "2s"],
  "n_opponents": 1,
  "pot": 100,
  "to_call": 20,
  "n_sims": 10000
}
```
Sortie :
```json
{
  "equity": 0.62,
  "win": 0.60,
  "tie": 0.04,
  "pot_odds": 0.167,
  "ev": {"fold": 0, "call": 54.4},
  "recommendation": "call"
}
```
Erreurs : `400` + `{"error": "..."}` (carte invalide, doublon, board de taille 1, 2 ou > 5…).

`GET /api/health` → `{"status": "ok"}`

## Répartition

| Pôle | Responsable | Livrable MVP | Travaille contre |
|---|---|---|---|
| **A. Moteur** | … | `engine/cards.py` (parsing, deck), `engine/evaluator.py` (meilleure main de 5 parmi 7, catégorie + kickers), `engine/montecarlo.py` (tirage cartes adverses + board restant) | — |
| **B. Décision** | … | `decision/` : cote du pot, EV(fold)/EV(call), recommandation (raise en v2) + tests unitaires du moteur | `equity()` mocké |
| **C. API & tests** | … | App Flask, `/api/analyze`, validation des entrées, CORS, gestion d'erreurs, tests d'intégration, CI GitHub Actions | `engine` et `decision` mockés |
| **D. Front-end** | … | Formulaire (cartes, pot, mise, nb adversaires) + affichage (équité, cote, EV, recommandation), états chargement/erreur | JSON en dur conforme au contrat |

### Formules (pôle B)
- Cote du pot : `pot_odds = to_call / (pot + to_call)`
- EV(fold) = `0`
- EV(call) = `equity * (pot + to_call) - to_call`
- Recommandation : `call` si `equity > pot_odds`, sinon `fold`

### Points de vigilance
- **A** : version naïve correcte d'abord (21 combinaisons), optimisation ensuite. Tester chaque catégorie, les égalités et la quinte A-2-3-4-5.
- **B** : pôle le plus léger → renfort sur les tests et le Monte Carlo.
- **C** : vérifier les doublons main/board côté API, pas seulement côté front.
- **D** : afficher un état de chargement pendant la simulation et les erreurs 400.

## Jalons

- [ ] **Semaine 1** : bout en bout avec mocks (front → API → fausses données)
- [ ] **Semaine 2** : évaluateur testé + Monte Carlo branché (contrôle : AA vs main aléatoire ≈ 85 %)
- [ ] **Semaine 3** : décision branchée, cas d'erreur couverts, démo

## Workflow Git

- Une branche par pôle : `engine`, `decision`, `api`, `front`
- PR vers `main`, relue par au moins un autre membre
- La CI (pytest) doit passer avant tout merge

## Extensions (après le jalon 3)

- Modélisation de l'adversaire par une range de mains
- Multi-joueurs
- Mode entraînement évaluant les décisions de l'utilisateur