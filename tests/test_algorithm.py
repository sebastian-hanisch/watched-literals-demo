"""Kern gegen Handrechnung (DEMO-PLAYBOOK §1b): das Handbeispiel F2 aus dem Plan, Schritt für Schritt, und kleine Mini-Instanzen von Hand.

Zählweise: Besuch = eine Klausel wird angesehen, weil ein Literal von ihr falsch wurde; Lesezugriff = ein Literal einer Klausel wird nach seinem Wert gefragt.
F2 = K1 (¬x1 ∨ x2 ∨ x3), K2 (¬x1 ∨ ¬x2 ∨ x4), K3 (¬x2 ∨ ¬x4 ∨ x5), K4 (x1 ∨ x3 ∨ ¬x5), K5 (¬x3 ∨ x4 ∨ x5), K6 (¬x4 ∨ ¬x5 ∨ x2); Entscheidungen x1, dann x2."""

import pytest

import wlt_algorithm as A
from wlt_cdcl import Loeser

F2_FIXPUNKT = {1: True, 2: True, 4: True, 5: True}


def test_f2_naiv_von_hand(f2):
    """Naiv, je Besuch alle Literale bis zum ersten wahren: K1 3, K2 3 (x1); K2 3 (erzwingt x4), K3 3 (erzwingt x5) (x2); K3 3, K6 3 (x4); K4 1, K6 3 (x5) = 8 Besuche, 22 Lesezugriffe."""
    lauf = A.handpropagation(*f2, (1, 2), watch=False)
    assert [(s["wahr_geworden"], s["klausel"] + 1, s["ergebnis"], len(s["gelesen"])) for s in lauf.schritte] == [
        (1, 1, "ohne_wirkung", 3), (1, 2, "ohne_wirkung", 3), (2, 2, "einheit", 3), (2, 3, "einheit", 3),
        (4, 3, "erfuellt", 3), (4, 6, "erfuellt", 3), (5, 4, "erfuellt", 1), (5, 6, "erfuellt", 3)]
    assert (lauf.besuche, lauf.lesezugriffe, lauf.propagationen) == (8, 22, 4)
    assert lauf.belegung == F2_FIXPUNKT and lauf.konflikt is None
    assert [i + 1 for i in lauf.nie_besucht] == [5]


def test_f2_watched_von_hand(f2):
    """Watched, Anfangsbeobachter die ersten zwei Literale: x1: K1 wandert (x2 frei, x3 frei) auf x3, K2 wandert auf x4; x2: K2 Einheit (erzwingt x4), K3 wandert auf x5;
    x4: K3 Einheit (erzwingt x5), K6 wandert auf x2; x5: K6 (x2 wahr, 1 Lesezugriff) = 7 Besuche, 13 Lesezugriffe; K4 und K5 werden nie angesehen."""
    lauf = A.handpropagation(*f2, (1, 2), watch=True)
    assert [(s["wahr_geworden"], s["klausel"] + 1, s["ergebnis"], len(s["gelesen"])) for s in lauf.schritte] == [
        (1, 1, "beobachter", 2), (1, 2, "beobachter", 2), (2, 2, "einheit", 2), (2, 3, "beobachter", 2),
        (4, 3, "einheit", 2), (4, 6, "beobachter", 2), (5, 6, "erfuellt", 1)]
    assert [(s["beobachter_vorher"], s["beobachter_nachher"]) for s in lauf.schritte] == [
        ((-1, 2), (2, 3)), ((-1, -2), (-2, 4)), ((-2, 4), (-2, 4)), ((-2, -4), (-4, 5)), ((-4, 5), (-4, 5)), ((-4, -5), (-5, 2)), ((-5, 2), (-5, 2))]
    assert [s["neues_literal"] for s in lauf.schritte] == [3, 4, 4, 5, 5, 2, None]
    assert (lauf.besuche, lauf.lesezugriffe, lauf.propagationen) == (7, 13, 4)
    assert lauf.belegung == F2_FIXPUNKT and lauf.konflikt is None
    assert [i + 1 for i in lauf.nie_besucht] == [4, 5]


def test_f2_summen_stimmen_mit_der_laufenden_summe_der_schritte(f2):
    for w in (False, True):
        lauf = A.handpropagation(*f2, (1, 2), watch=w)
        assert lauf.schritte[-1]["besuche"] == lauf.besuche and lauf.schritte[-1]["lesezugriffe"] == lauf.lesezugriffe
        assert sum(len(s["gelesen"]) for s in lauf.schritte) == lauf.lesezugriffe


def test_mini_instanz_mit_klauseln_der_laenge_zwei_von_hand():
    """(¬x1 ∨ x2), (¬x2 ∨ x3), Entscheidung x1. Watched: K1 beobachtet ¬x1 und x2, x2 frei, nichts zu suchen (Länge 2): Einheit, 1 Lesezugriff;
    dann x2: K2 (¬x2, x3): x3 frei, Einheit, 1 Lesezugriff: 2 Besuche, 2 Lesezugriffe. Naiv: K1 liest ¬x1 und x2 (2), K2 liest ¬x2 und x3 (2): 2 Besuche, 4 Lesezugriffe."""
    klauseln = [(-1, 2), (-2, 3)]
    w, n = A.handpropagation(3, klauseln, (1,), True), A.handpropagation(3, klauseln, (1,), False)
    assert (w.besuche, w.lesezugriffe) == (2, 2) and (n.besuche, n.lesezugriffe) == (2, 4)
    assert w.belegung == n.belegung == {1: True, 2: True, 3: True}
    assert all(len(s["gelesen"]) == 1 for s in w.schritte)


def test_klausel_der_laenge_eins_ist_fuer_die_handpropagation_verboten_aber_die_suche_loest_sie():
    with pytest.raises(ValueError):
        A.handpropagation(2, [(1,), (-1, 2)], (2,), True)
    r = A.vergleiche(3, [(1,), (-1, 2), (-2, 3)])
    for modus in ("naiv", "watch"):
        assert r[modus].antwort is True and r[modus].modell_ok is True


def test_konflikt_gleich_nach_der_ersten_entscheidung():
    """(¬x1 ∨ x2), (¬x1 ∨ ¬x2), Entscheidung x1: K1 erzwingt x2, K2 ist dann verletzt: Konflikt, der Lauf endet."""
    for w in (True, False):
        lauf = A.handpropagation(2, [(-1, 2), (-1, -2)], (1, 2), w)
        assert lauf.konflikt == 1 and lauf.log[-1] == ("abbruch", 1)
        assert lauf.schritte[-1]["ergebnis"] == "konflikt"


def test_entscheidung_auf_belegte_variable_wird_uebersprungen(f2):
    lauf = A.handpropagation(*f2, (1, 2, 4, 3), watch=True)           # x4 ist nach x2 schon erzwungen
    assert ("uebersprungen", 4) in lauf.log
    assert lauf.belegung[3] is True


@pytest.mark.parametrize("seed", range(6))
def test_handpropagation_zaehlt_wie_der_loeser(seed):
    """Die Einzelschritt-Ansicht und `Loeser.propagiere` führen zu denselben Zählern und derselben Belegung."""
    import wlt_instanzen as I
    inst = I.rand3(10, 40, seed)
    for w in (True, False):
        lauf = A.handpropagation(10, inst.klauseln, (3, -5, 7), w)
        s = Loeser(10, inst.klauseln, watch=w)
        konflikt = None
        for lit in (3, -5, 7):
            if s.wert[abs(lit)] == 0:
                s.entscheide(lit)
                konflikt = s.propagiere()
                if konflikt is not None:
                    break
        assert (lauf.besuche, lauf.lesezugriffe, lauf.propagationen) == (s.stat["besuche"], s.stat["lesezugriffe"], s.stat["propagationen"])
        assert lauf.konflikt == konflikt
        assert lauf.belegung == {v: s.wert[v] == 1 for v in range(1, 11) if s.wert[v] != 0}


def test_vergleiche_liefert_beide_modi_mit_gleicher_antwort():
    r = A.vergleiche(5, [(-1, 2, 3), (-1, -2, 4), (-2, -4, 5), (1, 3, -5), (-3, 4, 5), (-4, -5, 2)])
    assert r["naiv"].antwort is True and r["watch"].antwort is True
    assert r["naiv"].modell_ok and r["watch"].modell_ok
    assert sum(r["watch"].besuche_nach.values()) == r["watch"].besuche
    assert sum(r["naiv"].besuche_nach.values()) == r["naiv"].besuche
