"""Randfälle, an denen Propagation und Zählung erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): Klauseln der Länge 1 und 2, doppelte Literale, Tautologie,
leere Klausel, Konflikt gleich nach der ersten Entscheidung, lange Klauseln (Schubfach), leere Entscheidungsfolge, Budget."""

import pytest

import wlt_algorithm as A
import wlt_evaluation as ev
import wlt_instanzen as I


@pytest.mark.parametrize("watch", [False, True])
def test_doppelte_literale_und_tautologie(watch):
    """(x1 ∨ x1 ∨ x2) zählt wie (x1 ∨ x2); die Tautologie (x1 ∨ ¬x1 ∨ x3) fällt weg und wird nie besucht."""
    r = A.vergleiche(3, [(1, 1, 2), (1, -1, 3), (-1, 2)])
    assert r["naiv" if not watch else "watch"].antwort is True
    lauf = A.handpropagation(3, [(1, 2, 2), (-1, 2)], (1,), watch)
    assert lauf.belegung == {1: True, 2: True}
    with pytest.raises(ValueError):
        A.handpropagation(3, [(1, -1, 3), (-1, 2)], (1,), watch)      # Tautologie: der Löser verwirft sie, die Klauselnummern würden sich verschieben


@pytest.mark.parametrize("watch", [False, True])
def test_leere_klausel_ist_unerfuellbar(watch):
    r = A.vergleiche(2, [(1, 2), ()])
    assert r["naiv"].antwort is False and r["watch"].antwort is False
    assert r["naiv"].besuche == 0 and r["watch"].besuche == 0


def test_leere_formel_und_leere_entscheidungsfolge(f2):
    r = A.vergleiche(3, [])
    assert r["naiv"].antwort is True and r["watch"].antwort is True and r["naiv"].lesezugriffe == 0
    lauf = A.handpropagation(*f2, (), watch=True)
    assert lauf.schritte == [] and lauf.belegung == {} and lauf.besuche == lauf.lesezugriffe == 0
    assert [i + 1 for i in lauf.nie_besucht] == [1, 2, 3, 4, 5, 6]


def test_konflikt_nach_der_ersten_entscheidung_in_zwei_klauseln():
    """(¬x1 ∨ x2), (¬x1 ∨ ¬x2): Entscheidung x1 führt sofort in den Konflikt; ohne weitere Entscheidung ist x1 = falsch möglich, die Suche sagt erfüllbar."""
    klauseln = [(-1, 2), (-1, -2)]
    for w in (False, True):
        assert A.handpropagation(2, klauseln, (1,), w).konflikt is not None
    r = A.vergleiche(2, klauseln)
    assert r["naiv"].antwort is True and r["watch"].antwort is True and r["watch"].modell_ok


def test_lange_klauseln_schubfach_lesegrenzen():
    """Schubfach h = 4 hat Klauseln der Länge 4 (mindestens ein Loch): Watched liest je Besuch höchstens 3 Literale, naiv höchstens 4."""
    inst = I.pigeonhole(4)
    for w, grenze in ((True, 3), (False, 4)):
        lauf = A.handpropagation(inst.n, inst.klauseln, (1, 6, 11), w)
        assert lauf.schritte and max(len(s["gelesen"]) for s in lauf.schritte) <= grenze


def test_budget_erreicht_wird_als_abbruch_ausgewiesen():
    inst = I.pigeonhole(5)
    r = A.vergleiche(inst.n, inst.klauseln, budget=3)
    assert r["naiv"].antwort is None and r["watch"].antwort is None
    assert ev.verdict_kernfrage(r["naiv"], r["watch"])[0] == "warning"


def test_faktor_ohne_lesezugriffe_hat_keinen_wert():
    assert ev.faktor(10, 0) is None
    assert ev.faktor(0, 5) == 0.0
    r = A.vergleiche(3, [])                               # keine Klausel: kein Lesezugriff, kein Faktor
    z = ev.zeile("leer", 1, [r])
    assert z["formeln"] == 1 and z["faktor"] is None and z["faktor_min"] is None and z["faktor_unter_1"] == 0
    assert ev.verdict_kernfrage(r["naiv"], r["watch"])[0] == "info"
