"""Jede Zahl der README an den festen Formeln und Zufalls-Seeds (SplitMix64, ganzzahlige Zähler: auf jeder Plattform dieselben Werte, deshalb exakte Vergleiche).

Messreihen: zehn feste Formeln je Größe (Zufalls-Seeds 7000 bis 7009), Schubfach eine Formel je h. Gemessen wird in Besuchen und Lesezugriffen, nie in Sekunden.
Die Zeile Schubfach h = 7 liegt vorgerechnet in `wlt_messreihen.json`; ihre naive Hälfte (rund drei bis fünf Minuten) prüft `WLT_LANGSAM=1 pytest tests/test_claims.py -k vorgerechnet`."""

import functools
import json
import os
from pathlib import Path

import pytest

import wlt_algorithm as A
import wlt_constants as C
import wlt_evaluation as ev
import wlt_scenario as S

ROOT = Path(__file__).resolve().parent.parent


@functools.lru_cache(maxsize=None)
def reihe(familie):
    return {z["groesse"]: z for z in ev.messreihe(familie)}


def kennzahlen(z):
    return (z["naiv"]["lesezugriffe"], z["watch"]["lesezugriffe"])


# ------------------------------------------------------------------------------------------------------------------------------ Handbeispiel

def test_claim_handbeispiel_f2():
    n, w = A.handpropagation(C.F2_N, C.F2_KLAUSELN, C.F2_ENTSCHEIDUNGEN, False), A.handpropagation(C.F2_N, C.F2_KLAUSELN, C.F2_ENTSCHEIDUNGEN, True)
    assert (n.besuche, n.lesezugriffe) == (8, 22) and (w.besuche, w.lesezugriffe) == (7, 13)
    assert n.belegung == w.belegung == {1: True, 2: True, 4: True, 5: True}
    assert [i + 1 for i in n.nie_besucht] == [5] and [i + 1 for i in w.nie_besucht] == [4, 5]


# ------------------------------------------------------------------------------------------------------------------------------ Zufalls-3-SAT

ZUFALL = {
    # n: (Lesezugriffe naiv, Watched, Faktor, je Propagation naiv, Watched, Konflikte naiv, Watched, abweichende Formeln, erfüllbar)
    40: (61634, 24741, "2,5", "17,9", "7,4", 272, 246, 8, 7),
    60: (231675, 86079, "2,7", "22,6", "7,8", 595, 651, 10, 7),
    80: (592882, 142176, "4,2", "27,3", "7,9", 1109, 874, 9, 7),
    100: (2632463, 655877, "4,0", "44,9", "9,3", 2537, 2945, 9, 6),
    120: (25913527, 2895814, "8,9", "108,8", "13,0", 9051, 8399, 10, 5),
}


@pytest.mark.parametrize("n", list(ZUFALL))
def test_claim_zufall_messreihe(n):
    z = reihe(C.FAMILIE_ZUFALL)[n]
    ln, lw, f, jn, jw, kn, kw, abw, erf = ZUFALL[n]
    assert kennzahlen(z) == (ln, lw) and ev.de(z["faktor"], 1) == f
    assert (ev.de(ev.je_propagation_summe(z["naiv"]), 1), ev.de(ev.je_propagation_summe(z["watch"]), 1)) == (jn, jw)
    assert (z["naiv"]["konflikte"], z["watch"]["konflikte"]) == (kn, kw)
    assert z["konflikte_abweichend"] == abw and z["erfuellbar"] == erf
    assert z["antwort_gleich"] == z["formeln"] == 10 and z["abbrueche"] == 0


def test_claim_zufall_faktor_waechst_nicht_in_jedem_schritt_aber_je_propagation_naiv_in_jedem():
    z = reihe(C.FAMILIE_ZUFALL)
    faktoren = [z[n]["faktor"] for n in C.SWEEP_ZUFALL_N]
    assert faktoren[3] < faktoren[2]                                                  # n = 100 liegt unter n = 80 (4,0 gegen 4,2)
    naiv = [ev.je_propagation_summe(z[n]["naiv"]) for n in C.SWEEP_ZUFALL_N]
    watch = [ev.je_propagation_summe(z[n]["watch"]) for n in C.SWEEP_ZUFALL_N]
    assert all(b > a for a, b in zip(naiv, naiv[1:])) and all(b > a for a, b in zip(watch, watch[1:]))
    assert (ev.de(naiv[-1] / naiv[0], 1), ev.de(watch[-1] / watch[0], 1)) == ("6,1", "1,7")        # n = 120 gegen n = 40, je Propagation


def test_claim_zufall_n100_band_je_formel_und_zwei_formeln_unter_eins():
    z = reihe(C.FAMILIE_ZUFALL)[100]
    assert (ev.de(z["faktor_min"], 2), ev.de(z["faktor_max"], 1), z["faktor_unter_1"]) == ("0,20", "14,4", 2)
    unter = []
    for f in ev.formeln_der_familie(C.FAMILIE_ZUFALL, 100):
        r = A.vergleiche(f.n, f.klauseln)
        if r["naiv"].lesezugriffe < r["watch"].lesezugriffe:
            unter.append((f.name.split()[-1], r["naiv"].konflikte, r["watch"].konflikte, r["naiv"].propagationen, r["watch"].propagationen))
        # je Propagation liest Watched in jeder der zehn Formeln weniger als die Hälfte so viel wie naiv (kleinster Faktor 1,9, Formel 7009)
        assert ev.je_propagation(r["naiv"]) / ev.je_propagation(r["watch"]) > 1.9
    assert unter == [("7003", 84, 257, 2079, 6059), ("7009", 39, 438, 1120, 10776)]


# ------------------------------------------------------------------------------------------------------------------------------ Rampen

RAMPEN = {
    # n: (Lesezugriffe naiv, Watched, Faktor, je Propagation naiv, Watched, Konflikte naiv, Watched, abweichende Formeln, erfüllbar)
    20: (11864, 6519, "1,8", "4,9", "2,7", 102, 102, 0, 1),
    40: (23657, 12431, "1,9", "5,3", "2,8", 124, 124, 0, 2),
    60: (54181, 27567, "2,0", "5,4", "2,8", 181, 177, 2, 5),
    80: (254134, 106086, "2,4", "7,8", "3,2", 480, 496, 4, 2),
    100: (291555, 105177, "2,8", "8,9", "3,1", 423, 436, 3, 4),
}


@pytest.mark.parametrize("n", list(RAMPEN))
def test_claim_rampen_messreihe(n):
    z = reihe(C.FAMILIE_RAMPEN)[n]
    ln, lw, f, jn, jw, kn, kw, abw, erf = RAMPEN[n]
    assert kennzahlen(z) == (ln, lw) and ev.de(z["faktor"], 1) == f
    assert (ev.de(ev.je_propagation_summe(z["naiv"]), 1), ev.de(ev.je_propagation_summe(z["watch"]), 1)) == (jn, jw)
    assert (z["naiv"]["konflikte"], z["watch"]["konflikte"]) == (kn, kw)
    assert z["konflikte_abweichend"] == abw and z["erfuellbar"] == erf
    assert z["antwort_gleich"] == z["formeln"] == 10 and z["abbrueche"] == 0


def test_claim_rampen_faktor_waechst_in_jedem_schritt_und_bleibt_unter_dem_zufall_bei_gleichem_aufwand():
    z = reihe(C.FAMILIE_RAMPEN)
    faktoren = [z[n]["faktor"] for n in C.SWEEP_RAMPEN_N]
    assert all(b > a for a, b in zip(faktoren, faktoren[1:])) and max(faktoren) < 3.0 and min(faktoren) > 1.8
    assert all(z[n]["faktor_unter_1"] == 0 for n in z)                              # in keiner der 50 Formeln liest Watched mehr
    assert all(2.7 <= ev.je_propagation_summe(z[n]["watch"]) < 3.3 for n in z)


# ------------------------------------------------------------------------------------------------------------------------------ Schubfach

SCHUBFACH = {
    # h: (Lesezugriffe naiv, Watched, Faktor, je Propagation naiv, Watched, Konflikte naiv, Watched)
    3: (213, 124, "1,7", "3,9", "2,3", 7, 7),
    4: (2190, 1140, "1,9", "7,4", "3,8", 28, 28),
    5: (110397, 22861, "4,8", "58,9", "12,5", 160, 159),
    6: (8065528, 755871, "10,7", "573,0", "57,7", 1057, 1004),
}


@pytest.mark.parametrize("h", list(SCHUBFACH))
def test_claim_schubfach_live(h):
    z = reihe(C.FAMILIE_SCHUBFACH)[h]
    ln, lw, f, jn, jw, kn, kw = SCHUBFACH[h]
    assert kennzahlen(z) == (ln, lw) and ev.de(z["faktor"], 1) == f
    assert (ev.de(ev.je_propagation_summe(z["naiv"]), 1), ev.de(ev.je_propagation_summe(z["watch"]), 1)) == (jn, jw)
    assert (z["naiv"]["konflikte"], z["watch"]["konflikte"]) == (kn, kw)
    assert z["antwort_gleich"] == 1 and z["erfuellbar"] == 0 and z["abbrueche"] == 0


def _vorgerechnet():
    return {z["groesse"]: z for z in ev.vorgerechnete_zeilen()}


def test_claim_schubfach_vorgerechnete_zeilen_gleichen_der_neumessung_fuer_h3_bis_h6():
    vor = _vorgerechnet()
    assert sorted(vor) == [3, 4, 5, 6, 7] and all(z["vorgerechnet"] for z in vor.values())
    for h in (3, 4, 5, 6):
        live = reihe(C.FAMILIE_SCHUBFACH)[h]
        for schluessel in ("naiv", "watch", "faktor", "faktor_je_propagation", "formeln", "konflikte_abweichend", "antwort_gleich", "erfuellbar", "abbrueche"):
            assert vor[h][schluessel] == live[schluessel], (h, schluessel)


def test_claim_schubfach_h7_vorgerechnet_zahlen():
    z = _vorgerechnet()[7]
    assert kennzahlen(z) == (842295340, 17895735) and ev.de(z["faktor"], 1) == "47,1"
    assert (z["naiv"]["konflikte"], z["watch"]["konflikte"]) == (8433, 4811)
    assert z["antwort_gleich"] == 1 and z["abbrueche"] == 0 and z["erfuellbar"] == 0           # beide Verfahren: unerfüllbar, Budget nicht erreicht
    assert (z["naiv"]["propagationen"], z["watch"]["propagationen"]) == (111315, 63653)
    assert (z["naiv"]["besuche"], z["watch"]["besuche"]) == (120843892, 6504952)
    assert (ev.de(ev.je_propagation_summe(z["naiv"]), 1), ev.de(ev.je_propagation_summe(z["watch"]), 1), ev.de(z["faktor_je_propagation"], 1)) == ("7.566,8", "281,1", "26,9")
    # Zerlegung: 18,6-mal so viele Besuche und 7,0 gegen 2,8 Literale je Besuch
    assert ev.de(z["naiv"]["besuche"] / z["watch"]["besuche"], 1) == "18,6"
    assert (ev.de(z["naiv"]["lesezugriffe"] / z["naiv"]["besuche"], 1), ev.de(z["watch"]["lesezugriffe"] / z["watch"]["besuche"], 1)) == ("7,0", "2,8")


def test_claim_schubfach_h7_watched_live_gleicht_der_vorgerechneten_zeile():
    from wlt_cdcl import solve
    f = S.make_formel(C.FAMILIE_SCHUBFACH, h=7)
    r = solve(f.n, f.klauseln, watch=True, conflict_budget=C.BUDGET)             # nur Watched: das naive Verfahren braucht rund drei bis fünf Minuten
    w = _vorgerechnet()[7]["watch"]
    s = r.stat
    assert (s["propagationen"], s["besuche"], s["lesezugriffe"], s["konflikte"]) == (w["propagationen"], w["besuche"], w["lesezugriffe"], w["konflikte"])
    assert r.antwort is False


@pytest.mark.skipif(not os.environ.get("WLT_LANGSAM"), reason="rund drei bis fünf Minuten Rechenzeit; mit WLT_LANGSAM=1 einschalten")
def test_claim_schubfach_h7_naiv_vorgerechnet_gleicht_der_neumessung():
    f = S.make_formel(C.FAMILIE_SCHUBFACH, h=7)
    r = A.vergleiche(f.n, f.klauseln)["naiv"]
    n = _vorgerechnet()[7]["naiv"]
    assert (r.propagationen, r.besuche, r.lesezugriffe, r.konflikte) == (n["propagationen"], n["besuche"], n["lesezugriffe"], n["konflikte"])
    assert r.antwort is False


def test_claim_schubfach_faktor_waechst_in_jedem_schritt_von_h3_bis_h7():
    faktoren = [z["faktor"] for h, z in sorted(_vorgerechnet().items())]
    assert all(b > a for a, b in zip(faktoren, faktoren[1:])) and faktoren[0] < 2 and faktoren[-1] > 47


def test_claim_messreihendatei_hat_die_felder_die_die_app_liest():
    daten = json.loads((ROOT / C.MESSREIHEN_DATEI).read_text(encoding="utf-8"))
    assert daten["budget"] == C.BUDGET and len(daten["schubfach"]) == 5
    assert {z["label"] for z in daten["schubfach"]} == {f"Schubfach, Löcher h = {h}" for h in range(3, 8)}
    assert ev.messreihe_schubfach_mit_vorgerechnet()[-1]["groesse"] == 7


# ------------------------------------------------------------------------------------------------------------------------------ Gleiche Antwort, andere Zahl

def test_claim_fixpunkt_probe_200_von_200_in_vier_familien():
    erwartet = {  # Konflikt in beiden Modi
        C.FAMILIE_F2: 9, C.FAMILIE_ZUFALL: 0, C.FAMILIE_RAMPEN: 12, C.FAMILIE_SCHUBFACH: 2,
    }
    formeln = {C.FAMILIE_F2: S.make_formel(C.FAMILIE_F2), C.FAMILIE_ZUFALL: S.make_formel(C.FAMILIE_ZUFALL, 100, 4.26, seed=7000),
               C.FAMILIE_RAMPEN: S.make_formel(C.FAMILIE_RAMPEN, 60, 4.5, seed=7000), C.FAMILIE_SCHUBFACH: S.make_formel(C.FAMILIE_SCHUBFACH, h=6)}
    for familie, f in formeln.items():
        p = A.fixpunkt_probe(f.n, f.klauseln)
        assert p["proben"] == p["gleich"] == 200 and p["abweichungen"] == [] and p["konflikt_beide"] == erwartet[familie], familie


def test_claim_antwort_gleich_in_allen_zellen_der_messreihen():
    for familie in (C.FAMILIE_ZUFALL, C.FAMILIE_RAMPEN, C.FAMILIE_SCHUBFACH):
        for z in reihe(familie).values():
            assert z["antwort_gleich"] == z["formeln"]


# ------------------------------------------------------------------------------------------------------------------------------ Was tut ein Besuch?

BESUCH = {  # Fall: (Watched „Klausel erfüllt“ in %, naiv „ohne Wirkung“ in %)
    "Zufalls-3-SAT n = 100": ("34,8", "28,7"),
    "Rampen n = 60": ("34,3", "18,7"),
    "Schubfach h = 5": ("46,0", "16,9"),
    "Schubfach h = 6": ("55,5", "9,4"),
}


def test_claim_besuche_nach_ergebnis():
    faelle = {z["label"]: z for z in ev.besuch_faelle()}
    assert set(faelle) == set(BESUCH)
    for name, (erfuellt, ohne) in BESUCH.items():
        z = faelle[name]
        assert ev.de(100 * z["watch"]["besuche_nach"]["erfuellt"] / z["watch"]["besuche"], 1) == erfuellt, name
        assert ev.de(100 * z["naiv"]["besuche_nach"]["ohne_wirkung"] / z["naiv"]["besuche"], 1) == ohne, name
        assert z["watch"]["besuche_nach"]["ohne_wirkung"] == 0 and z["naiv"]["besuche_nach"]["beobachter"] == 0
        assert sum(z["watch"]["besuche_nach"].values()) == z["watch"]["besuche"] and sum(z["naiv"]["besuche_nach"].values()) == z["naiv"]["besuche"]


def test_claim_ein_erfuellt_besuch_liest_bei_watched_genau_ein_literal():
    """Eigenschaft hinter der Aussage „genau ein Literal“: jeder Watched-Besuch mit dem Ergebnis „erfüllt“ liest genau ein Literal (über 40 Formeln und Entscheidungsfolgen)."""
    import wlt_instanzen as I
    gesehen = 0
    for seed in range(40):
        inst = I.rand3(12, 45, seed)
        lauf = A.handpropagation(12, inst.klauseln, (1, -4, 7, -9), True)
        for s in lauf.schritte:
            if s["ergebnis"] == "erfuellt":
                assert len(s["gelesen"]) == 1
                gesehen += 1
    assert gesehen > 20
