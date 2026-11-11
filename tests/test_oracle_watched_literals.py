"""Orakel-Test watched-literals-demo: die Propagation gegen unabhängige Rechenwege (ORACLE-PLAYBOOK §5).

Orakel 1 (`referenz_propagation`): eine eigene, in diesem Test geschriebene Einheitspropagation ohne Code aus `wlt_cdcl.py`, mit der Zählregel des Plans (Besuch,
Lesezugriff) für beide Modi, nach dem Muster des Handbeispiel-Skripts der Planung. Verglichen werden Fixpunkt, Konflikt, Besuche und Lesezugriffe auf 200 zufälligen Formeln
mit zufälligen Entscheidungsfolgen (Zufalls-Seeds fest, SplitMix64).
Orakel 2 (`einfache_propagation`): Fixpunkt durch wiederholtes Durchsuchen aller Klauseln, ohne Warteschlange und ohne Beobachter (die einfachste mögliche Definition).
Orakel 3: OR-Tools CP-SAT für die Antwort der ganzen Suche (nur im Test).
Dazu Eigenschaften: Invariante der Beobachter, Lesezugriffe ≥ Besuche, Lesegrenzen je Besuch, Umbenennen der Variablen, Beobachter nach dem Zurückspringen."""

import pytest

import wlt_algorithm as A
import wlt_instanzen as I
from wlt_cdcl import Loeser, solve
from wlt_rng import SplitMix64


def _wert(wert, lit):
    v = abs(lit)
    return None if v not in wert else (wert[v] == (lit > 0))


def referenz_propagation(n, klauseln, folge, watch):
    """Entscheidungen nacheinander, je bis zum Fixpunkt. Rückgabe: (Belegung, Konflikt?, Besuche, Lesezugriffe, Propagationen)."""
    kl = [list(c) for c in klauseln]
    wert, trail = {}, []
    besuche = lesen = props = 0
    occ = {l: [i for i, c in enumerate(kl) if l in c] for v in range(1, n + 1) for l in (v, -v)}
    watches = {l: [] for v in range(1, n + 1) for l in (v, -v)}
    if watch:
        for i, c in enumerate(kl):
            watches[c[0]].append(i)
            watches[c[1]].append(i)

    def setze(l):
        wert[abs(l)] = l > 0
        trail.append(l)

    kopf = 0
    for d in folge:
        if abs(d) in wert:
            continue
        setze(d)
        while kopf < len(trail):
            p = trail[kopf]
            kopf += 1
            props += 1
            if not watch:
                for i in occ[-p]:
                    besuche += 1
                    frei, erfuellt = [], False
                    for l in kl[i]:
                        lesen += 1
                        w = _wert(wert, l)
                        if w is True:
                            erfuellt = True
                            break
                        if w is None:
                            frei.append(l)
                    if erfuellt:
                        continue
                    if not frei:
                        return wert, True, besuche, lesen, props
                    if len(frei) == 1:
                        setze(frei[0])
            else:
                for i in list(watches[-p]):
                    besuche += 1
                    c = kl[i]
                    if c[0] == -p:
                        c[0], c[1] = c[1], c[0]
                    lesen += 1
                    if _wert(wert, c[0]) is True:
                        continue
                    gefunden = False
                    for k in range(2, len(c)):
                        lesen += 1
                        if _wert(wert, c[k]) is not False:
                            c[1], c[k] = c[k], c[1]
                            watches[-p].remove(i)
                            watches[c[1]].append(i)
                            gefunden = True
                            break
                    if gefunden:
                        continue
                    if _wert(wert, c[0]) is False:
                        return wert, True, besuche, lesen, props
                    setze(c[0])
    return wert, False, besuche, lesen, props


def einfache_propagation(klauseln, folge):
    """Fixpunkt ohne Warteschlange: alle Klauseln durchsehen, bis sich nichts mehr ändert. Rückgabe: (Belegung, Konflikt?)."""
    wert = {}
    for d in folge:
        if abs(d) not in wert:
            wert[abs(d)] = d > 0
            while True:
                geaendert = False
                for c in klauseln:
                    if any(_wert(wert, l) is True for l in c):
                        continue
                    frei = [l for l in c if _wert(wert, l) is None]
                    if not frei:
                        return wert, True
                    if len(frei) == 1:
                        wert[abs(frei[0])] = frei[0] > 0
                        geaendert = True
                if not geaendert:
                    break
    return wert, False


def zufallsfall(i):
    rng = SplitMix64(1000 + i)
    n = 6 + rng.below(7)
    m = int(n * (2.0 + 3.0 * rng.random()))
    inst = I.rand3(n, m, 5000 + i)
    variablen = list(range(1, n + 1))
    rng.shuffle(variablen)
    folge = [v if rng.coin() else -v for v in variablen[: 1 + rng.below(min(n, 6))]]
    return n, inst.klauseln, folge


def kern_propagation(n, klauseln, folge, watch):
    s = Loeser(n, klauseln, watch=watch)
    konflikt = False
    for lit in folge:
        if s.wert[abs(lit)] != 0:
            continue
        s.entscheide(lit)
        if s.propagiere() is not None:
            konflikt = True
            break
    belegung = {v: s.wert[v] == 1 for v in range(1, n + 1) if s.wert[v] != 0}
    return s, belegung, konflikt


def test_zaehler_und_fixpunkt_gegen_die_referenz_auf_200_formeln():
    konflikte = 0
    for i in range(200):
        n, klauseln, folge = zufallsfall(i)
        for watch in (False, True):
            s, belegung, konflikt = kern_propagation(n, klauseln, folge, watch)
            ref_wert, ref_konflikt, ref_besuche, ref_lesen, ref_props = referenz_propagation(n, klauseln, folge, watch)
            assert konflikt == ref_konflikt, (i, watch)
            assert (s.stat["besuche"], s.stat["lesezugriffe"], s.stat["propagationen"]) == (ref_besuche, ref_lesen, ref_props), (i, watch)
            if not konflikt:
                assert belegung == ref_wert, (i, watch)
        konflikte += ref_konflikt
    assert 20 <= konflikte <= 180          # die Fälle decken Konflikte und konfliktfreie Läufe ab


def test_fixpunkt_beider_modi_gleicht_der_einfachsten_definition():
    for i in range(200):
        n, klauseln, folge = zufallsfall(i)
        einfach, einfach_konflikt = einfache_propagation(klauseln, folge)
        for watch in (False, True):
            _, belegung, konflikt = kern_propagation(n, klauseln, folge, watch)
            assert konflikt == einfach_konflikt, (i, watch)
            if not konflikt:
                assert belegung == einfach, (i, watch)


def test_naive_besuche_sind_die_vorkommen_aller_abgearbeiteten_literale():
    """Ohne Konflikt wird jedes belegte Literal p genau einmal abgearbeitet und besucht jede Klausel mit ¬p: Besuche = Summe der Vorkommen (zweiter Rechenweg)."""
    geprueft = 0
    for i in range(200):
        n, klauseln, folge = zufallsfall(i)
        s, belegung, konflikt = kern_propagation(n, klauseln, folge, False)
        if konflikt:
            continue
        erwartet = sum(sum(1 for c in klauseln if -(v if w else -v) in c) for v, w in belegung.items())
        assert s.stat["besuche"] == erwartet, i
        geprueft += 1
    assert geprueft >= 20


def test_invariante_der_beobachter_nach_der_propagation():
    """Ohne Konflikt: für jede Klausel sind beide beobachteten Literale nicht falsch, oder eines ist falsch und das andere wahr."""
    geprueft = 0
    for i in range(200):
        n, klauseln, folge = zufallsfall(i)
        s, _, konflikt = kern_propagation(n, klauseln, folge, True)
        if konflikt:
            continue
        for c in s.klauseln:
            a, b = s.wert_lit(c[0]), s.wert_lit(c[1])
            assert (a != -1 and b != -1) or (a == -1 and b == 1) or (b == -1 and a == 1), (i, c)
        geprueft += 1
    assert geprueft >= 20


def test_lesezugriffe_mindestens_besuche_und_lesegrenzen_je_besuch():
    for i in range(60):
        n, klauseln, folge = zufallsfall(i)
        for watch in (False, True):
            lauf = A.handpropagation(n, klauseln, folge, watch)
            assert lauf.lesezugriffe >= lauf.besuche
            laenge = {k: len(c) for k, c in enumerate(klauseln)}
            for s in lauf.schritte:
                gelesen, k = len(s["gelesen"]), laenge[s["klausel"]]
                assert 1 <= gelesen <= (k - 1 if watch else k)


def test_gleicher_fixpunkt_in_der_fixpunkt_probe_und_auf_strukturierten_formeln():
    for inst in (I.rand3(30, 110, 3), I.pigeonhole(4), I.rampen_instanz(20, 4.0, 1, 3)):
        probe = A.fixpunkt_probe(inst.n, inst.klauseln, 100, seed=7)
        assert probe["gleich"] == probe["proben"] == 100 and probe["abweichungen"] == []


def test_antwort_der_ganzen_suche_gegen_cpsat():
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")

    def cpsat(n, klauseln):
        m = cp_model.CpModel()
        x = [None] + [m.NewBoolVar(f"x{i}") for i in range(1, n + 1)]
        for c in klauseln:
            m.AddBoolOr([x[l] if l > 0 else x[-l].Not() for l in c])
        s = cp_model.CpSolver()
        s.parameters.num_workers = 1
        return s.Solve(m) in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    formeln = [I.rand3(40, int(4.26 * 40), s) for s in range(12)] + [I.pigeonhole(4), I.pigeonhole(5), I.rampen_instanz(30, 4.5, 2, 3)]
    antworten = set()
    for inst in formeln:
        referenz = cpsat(inst.n, inst.klauseln)
        antworten.add(referenz)
        r = A.vergleiche(inst.n, inst.klauseln)
        for modus in ("naiv", "watch"):
            assert r[modus].antwort is referenz, (inst.meta, modus)
            if referenz:
                assert r[modus].modell_ok is True
    assert antworten == {True, False}


def test_umbenennen_der_variablen_aendert_den_fixpunkt_nur_bis_auf_die_umbenennung():
    for i in range(40):
        n, klauseln, folge = zufallsfall(i)
        rng = SplitMix64(77 + i)
        perm = list(range(1, n + 1))
        rng.shuffle(perm)
        pi = {v: perm[v - 1] for v in range(1, n + 1)}
        um = [tuple((pi[abs(l)] if l > 0 else -pi[abs(l)]) for l in c) for c in klauseln]
        um_folge = [(pi[abs(l)] if l > 0 else -pi[abs(l)]) for l in folge]
        for watch in (False, True):
            _, b1, k1 = kern_propagation(n, klauseln, folge, watch)
            _, b2, k2 = kern_propagation(n, um, um_folge, watch)
            assert k1 == k2
            if not k1:
                assert {pi[v]: w for v, w in b1.items()} == b2


def test_beobachter_bleiben_nach_dem_zurueckspringen_gueltig():
    """Chaff: beim Zurückspringen müssen die Beobachter nicht angepasst werden. Hier: nach Rücksprung bleiben die Beobachter auf den Positionen 0 und 1
    und die Propagation findet denselben Fixpunkt wie bei frischem Beginn mit derselben Entscheidungsfolge."""
    for i in range(40):
        n, klauseln, folge = zufallsfall(i)
        s = Loeser(n, klauseln, watch=True)
        konflikt = False
        for lit in folge:
            if s.wert[abs(lit)] == 0:
                s.entscheide(lit)
                if s.propagiere() is not None:
                    konflikt = True
                    break
        s.springe_zurueck(0)
        s.qkopf = len(s.spur_lit)
        for lit in folge:
            if s.wert[abs(lit)] == 0:
                s.entscheide(lit)
                if s.propagiere() is not None:
                    break
        _, belegung, konflikt2 = kern_propagation(n, klauseln, folge, True)
        assert konflikt == konflikt2
        if not konflikt:
            assert {v: s.wert[v] == 1 for v in range(1, n + 1) if s.wert[v] != 0} == belegung


def test_gelernte_klauseln_waehrend_der_suche_halten_die_beobachter_auf_den_stufen_ueber_null():
    """Nach einer ganzen Suche mit Lernen: jede lebende Klausel hat ihre Beobachter auf Position 0 und 1 und steht in deren Beobachterlisten."""
    inst = I.rand3(50, 213, 11)
    s = Loeser(inst.n, inst.klauseln, watch=True)
    s.loese()
    assert s.stat["gelernt"] > 0
    for i, c in enumerate(s.klauseln):
        assert i in s.beobachtet[c[0]] and i in s.beobachtet[c[1]]


def test_beide_modi_geben_dieselbe_antwort_auf_zufallsformeln():
    for seed in range(15):
        inst = I.rand3(35, 150, seed)
        a, b = solve(inst.n, inst.klauseln, watch=True), solve(inst.n, inst.klauseln, watch=False)
        assert a.antwort == b.antwort
