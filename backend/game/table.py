"""Partie de Texas Hold'em No-Limit (mode JEU).

Une instance de `Game` = une table : joueurs, tapis, bouton, main en cours.
Toutes les mises sont en jetons entiers. Les montants de relance sont des
montants « à » (total misé sur la rue après l'action), comme en vrai.
"""
import random
from dataclasses import dataclass, field

from engine.cards import FULL_DECK
from engine.evaluator import CATEGORY_NAMES, category, evaluate

STREETS = ["preflop", "flop", "turn", "river"]
STREET_FR = {"flop": "Flop", "turn": "Turn", "river": "River"}


class IllegalAction(ValueError):
    pass


@dataclass
class Player:
    name: str
    is_bot: bool
    stack: int
    hole: list[str] = field(default_factory=list)
    bet: int = 0          # mise sur la rue en cours
    total: int = 0        # mise totale sur la main (pour les pots annexes)
    folded: bool = False
    all_in: bool = False
    acted: bool = False   # a parlé depuis la dernière relance complète
    shown: bool = False   # cartes montrées au showdown

    @property
    def in_hand(self) -> bool:
        return bool(self.hole) and not self.folded

    @property
    def can_act(self) -> bool:
        return self.in_hand and not self.all_in


class Game:
    def __init__(self, players: list[tuple[str, bool]], stack: int = 1000,
                 small_blind: int = 5, big_blind: int = 10, seed: int | None = None):
        if not 2 <= len(players) <= 10:
            raise ValueError("2 à 10 joueurs")
        self.players = [Player(n, b, stack) for n, b in players]
        self.sb, self.bb = small_blind, big_blind
        self.rng = random.Random(seed)
        self.button = self.rng.randrange(len(self.players))
        self.hand_no = 0
        self.board: list[str] = []
        self.deck: list[str] = []
        self.street = "preflop"
        self.current: int | None = None
        self.current_bet = 0
        self.min_raise = big_blind
        self.n_raises = 0  # relances sur la rue en cours (sert aux bots)
        self.hand_over = True
        self.results: list[dict] = []
        self.log: list[str] = []

    # ------------------------------------------------------------ utilitaires
    def _next(self, i: int, pred) -> int | None:
        n = len(self.players)
        for k in range(1, n + 1):
            j = (i + k) % n
            if pred(self.players[j]):
                return j
        return None

    def _say(self, msg: str):
        self.log.append(msg)
        self.log = self.log[-30:]

    @property
    def pot(self) -> int:
        return sum(p.total for p in self.players)

    @property
    def game_over(self) -> bool:
        return self.hand_over and sum(p.stack > 0 for p in self.players) <= 1

    def _put(self, p: Player, amount: int):
        amount = min(amount, p.stack)
        p.stack -= amount
        p.bet += amount
        p.total += amount
        if p.stack == 0:
            p.all_in = True

    # ------------------------------------------------------------ main
    def start_hand(self):
        if not self.hand_over:
            raise IllegalAction("Main déjà en cours")
        if self.game_over:
            raise IllegalAction("Partie terminée")
        self.hand_no += 1
        for p in self.players:
            p.hole, p.bet, p.total = [], 0, 0
            p.folded = p.all_in = p.acted = p.shown = False
        self.deck = FULL_DECK[:]
        self.rng.shuffle(self.deck)
        self.board, self.results, self.hand_over = [], [], False
        self.street = "preflop"

        seated = lambda p: p.stack > 0
        self.button = self._next(self.button, seated)
        in_play = [i for i, p in enumerate(self.players) if p.stack > 0]
        # distribution : deux tours en partant de la gauche du bouton
        order, j = [], self._next(self.button, seated)
        for _ in in_play:
            order.append(j)
            j = self._next(j, seated)
        for _ in range(2):
            for i in order:
                self.players[i].hole.append(self.deck.pop())

        if len(in_play) == 2:  # heads-up : le bouton est petite blinde
            sb_i = self.button
        else:
            sb_i = self._next(self.button, seated)
        bb_i = self._next(sb_i, seated)
        self._put(self.players[sb_i], self.sb)
        self._put(self.players[bb_i], self.bb)
        self._say(f"— Main n°{self.hand_no} — {self.players[sb_i].name} : petite blinde {self.sb}, "
                  f"{self.players[bb_i].name} : grosse blinde {self.bb}")
        self.current_bet = self.bb
        self.min_raise = self.bb
        self.n_raises = 0
        self.current = bb_i
        self._advance_turn()

    # ------------------------------------------------------------ actions
    def to_call(self, i: int | None = None) -> int:
        p = self.players[self.current if i is None else i]
        return min(self.current_bet - p.bet, p.stack)

    def legal(self) -> dict | None:
        if self.hand_over or self.current is None:
            return None
        p = self.players[self.current]
        tc = self.to_call()
        can_raise = not p.acted and p.stack > self.current_bet - p.bet
        max_to = p.bet + p.stack
        return {
            "fold": tc > 0,
            "check": tc == 0,
            "call": tc > 0,
            "call_amount": tc,
            "raise": {"min": min(self.current_bet + self.min_raise, max_to), "max": max_to} if can_raise else None,
        }

    def act(self, action: str, amount: int | None = None):
        legal = self.legal()
        if legal is None:
            raise IllegalAction("Ce n'est le tour de personne")
        p = self.players[self.current]

        if action == "fold":
            if not legal["fold"]:
                action = "check"  # se coucher sans mise à suivre = parole
            else:
                p.folded = True
                self._say(f"{p.name} se couche")
        if action == "check":
            if not legal["check"]:
                raise IllegalAction("Impossible de checker : il y a une mise à suivre")
            self._say(f"{p.name} checke")
        elif action == "call":
            if not legal["call"]:
                raise IllegalAction("Rien à suivre")
            self._put(p, legal["call_amount"])
            self._say(f"{p.name} suit {legal['call_amount']}" + (" (tapis)" if p.all_in else ""))
        elif action in ("raise", "allin"):
            r = legal["raise"]
            if r is None:
                if action == "allin" and legal["call"]:
                    return self.act("call")
                raise IllegalAction("Relance impossible")
            to = r["max"] if action == "allin" else int(amount if amount is not None else r["min"])
            if not r["min"] <= to <= r["max"]:
                raise IllegalAction(f"Relance entre {r['min']} et {r['max']}")
            increment = to - self.current_bet
            verb = "mise" if self.current_bet == 0 else "relance à"
            self._put(p, to - p.bet)
            if increment >= self.min_raise:  # relance complète : rouvre les enchères
                self.min_raise = increment
                for q in self.players:
                    q.acted = False
            self.current_bet = max(self.current_bet, p.bet)
            self.n_raises += 1
            self._say(f"{p.name} {verb} {to}" + (" (tapis)" if p.all_in else ""))
        elif action != "fold":
            raise IllegalAction(f"Action inconnue : {action}")

        p.acted = True
        self._advance_turn()

    # ------------------------------------------------------------ déroulement
    def _round_done(self) -> bool:
        return all(p.acted and p.bet == self.current_bet
                   for p in self.players if p.can_act)

    def _advance_turn(self):
        contenders = [p for p in self.players if p.in_hand]
        if len(contenders) == 1:
            return self._win_uncontested(contenders[0])

        if not self._round_done():
            nxt = self._next(self.current, lambda q: q.can_act and (not q.acted or q.bet < self.current_bet))
            if nxt is not None:
                self.current = nxt
                return

        # fin de la rue
        able = [p for p in contenders if p.can_act]
        if self.street == "river" or len(able) <= 1:
            while len(self.board) < 5:  # plus personne ne peut miser : on déroule le board
                self._deal_street()
            return self._showdown()
        self._deal_street()
        self.current = self._next(self.button, lambda q: q.can_act)

    def _deal_street(self):
        self.street = STREETS[STREETS.index(self.street) + 1]
        self.deck.pop()  # carte brûlée
        n = 3 if self.street == "flop" else 1
        self.board += [self.deck.pop() for _ in range(n)]
        for p in self.players:
            p.bet, p.acted = 0, False
        self.current_bet = 0
        self.min_raise = self.bb
        self.n_raises = 0
        self._say(f"{STREET_FR[self.street]} : {' '.join(self.board)}")

    def _finish(self):
        self.hand_over = True
        self.current = None
        for p in self.players:
            p.bet = 0

    def _win_uncontested(self, winner: Player):
        amount = self.pot
        winner.stack += amount
        self.results = [{"name": winner.name, "amount": amount, "hand_name": None}]
        self._say(f"{winner.name} remporte {amount}")
        self._finish()

    def _showdown(self):
        self.street = "showdown"
        contenders = [p for p in self.players if p.in_hand]
        scores = {id(p): evaluate(p.hole + self.board) for p in contenders}
        for p in contenders:
            p.shown = True

        won: dict[int, int] = {}
        levels = sorted({p.total for p in contenders})
        prev = 0
        for level in levels:  # pot principal puis pots annexes
            part = sum(min(p.total, level) - min(p.total, prev) for p in self.players)
            prev = level
            if part == 0:
                continue
            eligible = [p for p in contenders if p.total >= level]
            best = max(scores[id(p)] for p in eligible)
            winners = [p for p in eligible if scores[id(p)] == best]
            share, rest = divmod(part, len(winners))
            # jeton impair au premier gagnant à gauche du bouton
            order = sorted(winners, key=lambda p: (self.players.index(p) - self.button - 1) % len(self.players))
            for k, p in enumerate(order):
                won[id(p)] = won.get(id(p), 0) + share + (1 if k < rest else 0)
        # jetons misés au-delà de ce que quiconque pouvait couvrir (cas d'un joueur couché) : rendus
        leftover = self.pot - sum(won.values())
        if leftover:
            top = max(contenders, key=lambda p: p.total)
            won[id(top)] = won.get(id(top), 0) + leftover

        self.results = []
        for p in contenders:
            name = CATEGORY_NAMES[category(scores[id(p)])]
            amount = won.get(id(p), 0)
            p.stack += amount
            if amount:
                self._say(f"{p.name} remporte {amount} avec {name.lower()}")
            self.results.append({"name": p.name, "amount": amount, "hand_name": name})
        self._finish()

    # ------------------------------------------------------------ vue JSON
    def view(self, viewer: int | None = None) -> dict:
        """État pour le front. Seules les cartes de `viewer` (et celles montrées) sont visibles."""
        players = []
        for i, p in enumerate(self.players):
            visible = p.hole and (i == viewer or p.shown)
            players.append({
                "name": p.name, "bot": p.is_bot, "stack": p.stack, "bet": p.bet,
                "folded": p.folded, "all_in": p.all_in, "out": p.stack == 0 and not p.hole,
                "n_cards": len(p.hole) if not p.folded else 0,
                "hole": p.hole if visible else None,
            })
        legal = self.legal()
        return {
            "hand_no": self.hand_no, "street": self.street, "board": self.board,
            "pot": self.pot, "button": self.button, "current": self.current,
            "current_bet": self.current_bet, "sb": self.sb, "bb": self.bb,
            "players": players, "legal": legal,
            "hand_over": self.hand_over, "results": self.results,
            "game_over": self.game_over,
            "winner": next((p.name for p in self.players if p.stack > 0), None) if self.game_over else None,
            "log": self.log[-12:],
        }
