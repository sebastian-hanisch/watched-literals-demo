"""Kern der Demo: dieselbe Propagation mit und ohne beobachtete Literale (Watched Literals), Schritt für Schritt und über die ganze Suche.

Gerechnet wird mit dem kopierten CDCL (`wlt_cdcl.py`, Option `watch`); dieses Modul macht daraus die Ansichten der App:

  `handpropagation`    Entscheidungen setzen und bis zum Fixpunkt propagieren, jeder Klausel-Besuch mit gelesenen Literalen,
                       Beobachtern vorher und nachher und Ergebnis (die Schritt-für-Schritt-Ansicht)
  `vergleiche`         die ganze Suche (Lernen, Aktivität, Neustarts) in beiden Modi mit allen Zählern
  `fixpunkt_probe`     dieselben zufälligen Entscheidungsfolgen in beiden Modi: derselbe Fixpunkt?

Zählweise (gleich in beiden Modi): **Besuch** = eine Klausel wird angesehen, weil ein Literal von ihr falsch wurde;
**Lesezugriff** = ein Literal einer Klausel wird nach seinem Wert gefragt. Naiv liest ein Besuch die Literale der Reihe nach, bis ein wahres kommt;
mit Beobachtern liest ein Besuch zuerst das andere beobachtete Literal und sucht nur dann ab Position 3 ein nicht falsches Literal."""

from dataclasses import dataclass, field
from typing import NamedTuple

import wlt_constants as C
import wlt_instanzen as I
from wlt_cdcl import Loeser, solve
from wlt_rng import SplitMix64


class Lauf(NamedTuple):
    """Ergebnis einer ganzen Suche in einem Modus."""
    antwort: object              # True, False oder None (Budget erreicht)
    propagationen: int
    besuche: int
    lesezugriffe: int
    konflikte: int
    besuche_nach: dict           # erfuellt / beobachter / einheit / konflikt / ohne_wirkung
    modell_ok: object            # True/False: Modell erfüllt jede Klausel (unabhängig geprüft); None ohne Modell


@dataclass
class Handlauf:
    watch: bool
    klauseln: tuple
    schritte: list = field(default_factory=list)       # ein Eintrag je Klausel-Besuch (Wörterbuch)
    log: list = field(default_factory=list)            # Entscheidungen: ("entscheide", lit) / ("uebersprungen", lit) / ("abbruch", lit)
    besuche: int = 0
    lesezugriffe: int = 0
    propagationen: int = 0
    belegung: dict = field(default_factory=dict)       # Variable -> bool nach dem letzten Fixpunkt
    konflikt: object = None                            # 0-basierter Klauselindex der verletzten Klausel oder None
    nie_besucht: list = field(default_factory=list)    # 0-basierte Indizes der Klauseln, die kein Besuch angesehen hat


def _wert(wert, lit):
    """1 wahr, -1 falsch, 0 frei, für ein Literal bei gegebener Belegung `wert` (Variable -> 0/1/-1)."""
    w = wert[abs(lit)]
    return w if lit > 0 else -w


def _schritte_eines_literals(s: Loeser, p: int, vorher: list, wert: list, marke: int, lauf: Handlauf, entscheidung: int):
    """Wandelt die Besuchs-Ereignisse der Propagation des Literals p in Einträge der Ansicht um.

    `vorher`: Kopie der Klauseln vor dem Literal, `wert`: Kopie der Belegung (wird mit den Schlüssen fortgeschrieben, damit ein Besuch sieht,
    was die vorangehenden Besuche desselben Literals erzwungen haben)."""
    falsch = -p
    for e in s.ereignisse[marke:]:
        if e[0] == "schliesse":
            lit = e[1]
            wert[abs(lit)] = 1 if lit > 0 else -1
            continue
        if e[0] != "besuch":
            continue
        _, ci, paar, ergebnis, neu = e
        c = list(vorher[ci])
        gelesen = []                                   # (Literal, Wert 1/-1/0)
        if s.beobachter:
            vorn = (c[0], c[1])
            anderes = c[1] if c[0] == falsch else c[0]
            gelesen.append((anderes, _wert(wert, anderes)))
            if gelesen[-1][1] != 1:
                for k in range(2, len(c)):
                    gelesen.append((c[k], _wert(wert, c[k])))
                    if gelesen[-1][1] != -1:
                        break
            nachher = (anderes, neu) if ergebnis == "beobachter" else vorn
            beobachter_nachher = tuple(sorted(nachher, key=lambda l: c.index(l)))
            beobachter_vorher = vorn
        else:
            for l in c:
                gelesen.append((l, _wert(wert, l)))
                if gelesen[-1][1] == 1:
                    break
            beobachter_vorher = beobachter_nachher = None
        lauf.besuche += 1
        lauf.lesezugriffe += len(gelesen)
        lauf.schritte.append({
            "nr": len(lauf.schritte) + 1, "entscheidung": entscheidung, "wahr_geworden": p, "falsch_geworden": falsch,
            "klausel": ci, "literale": tuple(c), "beobachter_vorher": beobachter_vorher, "beobachter_nachher": beobachter_nachher,
            "gelesen": tuple(gelesen), "ergebnis": ergebnis, "neues_literal": neu,
            "besuche": lauf.besuche, "lesezugriffe": lauf.lesezugriffe,
        })


def _propagiere_einzeln(s: Loeser, lauf: Handlauf, entscheidung: int):
    """Wie `Loeser.propagiere`, aber ein Literal nach dem anderen, damit jeder Besuch dem auslösenden Literal zugeordnet werden kann.
    Rückgabe: Index der verletzten Klausel oder None. (tests/test_algorithm.py prüft, dass die Zähler denen von `propagiere` gleichen.)"""
    while s.qkopf < len(s.spur_lit):
        p = s.spur_lit[s.qkopf]
        s.qkopf += 1
        s.stat["propagationen"] += 1
        lauf.propagationen += 1
        vorher = [list(c) for c in s.klauseln]
        wert = list(s.wert)
        marke = len(s.ereignisse)
        konflikt = s._prop_beobachter(p) if s.beobachter else s._prop_naiv(p)
        _schritte_eines_literals(s, p, vorher, wert, marke, lauf, entscheidung)
        if konflikt is not None:
            return konflikt
    return None


def handpropagation(n: int, klauseln, entscheidungen, watch: bool) -> Handlauf:
    """Setzt die Entscheidungen der Reihe nach (jeweils bis zum Fixpunkt propagiert) und zeichnet jeden Klausel-Besuch auf.

    Eine Entscheidung auf eine schon belegte Variable wird übersprungen; bei einem Konflikt endet der Lauf. Voraussetzung: keine Klausel der Länge 1
    (sonst vereinfacht der Löser sie schon beim Aufnehmen und die Klauselnummern verschieben sich)."""
    klauseln = tuple(tuple(c) for c in klauseln)
    if any(len(set(c)) < 2 for c in klauseln):
        raise ValueError("die Handpropagation braucht Klauseln mit mindestens zwei verschiedenen Literalen")
    s = Loeser(n, klauseln, watch=watch, trace="besuche")
    lauf = Handlauf(watch, klauseln)
    if len(s.klauseln) != len(klauseln):
        raise ValueError("der Löser hat Klauseln beim Aufnehmen verworfen (Tautologie oder doppelte Literale)")
    for nr, lit in enumerate(entscheidungen, start=1):
        if s.wert[abs(lit)] != 0:
            lauf.log.append(("uebersprungen", lit))
            continue
        s.entscheide(lit)
        lauf.log.append(("entscheide", lit))
        k = _propagiere_einzeln(s, lauf, nr)
        if k is not None:
            lauf.konflikt = k
            lauf.log.append(("abbruch", lit))
            break
    lauf.belegung = {v: s.wert[v] == 1 for v in range(1, n + 1) if s.wert[v] != 0}
    besucht = {st["klausel"] for st in lauf.schritte}
    lauf.nie_besucht = [i for i in range(len(klauseln)) if i not in besucht]
    return lauf


def vergleiche(n: int, klauseln, budget: int = C.BUDGET) -> dict:
    """Die ganze Suche (Standardeinstellungen des CDCL, Zufall aus) in beiden Modi: {"naiv": Lauf, "watch": Lauf}."""
    klauseln = [tuple(c) for c in klauseln]
    ergebnis = {}
    for name, w in (("naiv", False), ("watch", True)):
        r = solve(n, klauseln, watch=w, conflict_budget=budget)
        st = r.stat
        ok = I.pruefe_modell(klauseln, r.modell) if r.antwort is True else None
        ergebnis[name] = Lauf(r.antwort, st["propagationen"], st["besuche"], st["lesezugriffe"], st["konflikte"], dict(st["besuche_nach"]), ok)
    return ergebnis


def fixpunkt_probe(n: int, klauseln, anzahl: int = C.PROBEN_FIXPUNKT, seed: int = 1, max_entscheidungen: int = 6) -> dict:
    """Zufällige Entscheidungsfolgen (je höchstens `max_entscheidungen` Entscheidungen auf verschiedene Variablen, zufälliges Vorzeichen), in beiden
    Modi bis zum Fixpunkt propagiert. Gleich heißt: beide finden einen Konflikt, oder keiner findet einen und die belegten Literale sind dieselben.
    Rückgabe: {"proben", "gleich", "konflikt_beide", "ohne_konflikt", "abweichungen"} (abweichungen: Liste der Entscheidungsfolgen)."""
    klauseln = [tuple(c) for c in klauseln]
    rng = SplitMix64(seed)
    gleich = konflikt_beide = 0
    abweichungen = []
    for _ in range(anzahl):
        variablen = list(range(1, n + 1))
        rng.shuffle(variablen)
        folge = [v if rng.coin() else -v for v in variablen[: 1 + rng.below(min(n, max_entscheidungen))]]
        ausgang = []
        for w in (False, True):
            s = Loeser(n, klauseln, watch=w)
            konflikt = not s.ok
            for lit in folge:
                if konflikt:
                    break
                if s.wert[abs(lit)] != 0:
                    continue
                s.entscheide(lit)
                konflikt = s.propagiere() is not None
            ausgang.append((konflikt, None if konflikt else frozenset(s.spur_lit)))
        if ausgang[0][0] and ausgang[1][0]:
            gleich += 1
            konflikt_beide += 1
        elif ausgang[0] == ausgang[1]:
            gleich += 1
        else:
            abweichungen.append(folge)
    return {"proben": anzahl, "gleich": gleich, "konflikt_beide": konflikt_beide, "ohne_konflikt": gleich - konflikt_beide, "abweichungen": abweichungen}
