"""Messreihe und Vergleich mit Fortschrittsanzeige und Zwischenspeicher: das Ergebnis ist gleich dem ungepufferten, ein anderer Parameter kommt nicht aus dem Speicher."""

import os

from streamlit.testing.v1 import AppTest

import wlt_algorithm as A
import wlt_constants as C
import wlt_evaluation as ev
import wlt_fortschritt as F
import wlt_scenario as S

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def test_zwischengespeicherte_messreihe_ist_gleich_der_ungepufferten():
    F.vergleich.clear()
    for familie in (C.FAMILIE_RAMPEN, C.FAMILIE_SCHUBFACH):
        direkt = ev.messreihe_schubfach_mit_vorgerechnet() if familie == C.FAMILIE_SCHUBFACH else ev.messreihe(familie)
        assert F.messreihe(familie) == direkt, familie
        assert F.messreihe(familie) == direkt, (familie, "zweiter Aufruf aus dem Zwischenspeicher")


def test_vergleich_einer_formel_ist_gleich_dem_ungepufferten():
    F.vergleich.clear()
    f = S.make_formel(C.FAMILIE_ZUFALL, n=40, dichte=4.26, seed=7003)
    assert F.vergleich(f.n, f.klauseln, C.BUDGET) == A.vergleiche(f.n, f.klauseln)
    assert F.vergleich(f.n, f.klauseln, C.BUDGET) == A.vergleiche(f.n, f.klauseln)


def test_feste_formeln_gleich_der_ungepufferten_fassung_der_app():
    F.vergleich.clear()
    for familie, n, dichte in ((C.FAMILIE_ZUFALL, 30, 4.26), (C.FAMILIE_RAMPEN, 30, 4.5), (C.FAMILIE_SCHUBFACH, 20, 2.0)):
        if familie in (C.FAMILIE_ZUFALL, C.FAMILIE_RAMPEN):
            formeln = [S.make_formel(familie, n=n, dichte=dichte, seed=s) for s in C.SWEEP_SEEDS]
        else:
            formeln = [S.make_formel(familie, n=n, dichte=dichte)]
        direkt = [(f.name, A.vergleiche(f.n, f.klauseln)) for f in formeln]
        assert F.feste_formeln(familie, n, dichte) == direkt, familie


def test_zweiter_aufruf_rechnet_nichts_neu_ein_anderer_parameter_schon():
    F.vergleich.clear()
    v0 = F.gerechnet()
    erste = F.feste_formeln(C.FAMILIE_RAMPEN, 30, 4.5)
    v1 = F.gerechnet()
    assert v1 - v0 == len(C.SWEEP_SEEDS)
    assert F.feste_formeln(C.FAMILIE_RAMPEN, 30, 4.5) == erste and F.gerechnet() == v1
    andere_dichte = F.feste_formeln(C.FAMILIE_RAMPEN, 30, 5.0)
    assert F.gerechnet() - v1 == len(C.SWEEP_SEEDS), "eine andere Dichte darf nicht aus dem Zwischenspeicher kommen"
    assert andere_dichte != erste
    v2 = F.gerechnet()
    andere_groesse = F.feste_formeln(C.FAMILIE_RAMPEN, 40, 4.5)
    assert F.gerechnet() - v2 == len(C.SWEEP_SEEDS) and andere_groesse != erste
    # dieselbe Formel mit anderem Budget ist ein anderer Eintrag
    f = S.make_formel(C.FAMILIE_RAMPEN, n=30, dichte=4.5, seed=C.SWEEP_SEEDS[0])
    v3 = F.gerechnet()
    F.vergleich(f.n, f.klauseln, C.BUDGET)
    assert F.gerechnet() == v3
    F.vergleich(f.n, f.klauseln, 50)
    assert F.gerechnet() == v3 + 1


def test_messreihe_und_vergleich_teilen_den_speicher_und_melden_jede_formel():
    F.vergleich.clear()
    meldungen = []
    F.messreihe(C.FAMILIE_SCHUBFACH, lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(i, len(C.SWEEP_SCHUBFACH_H)) for i in range(1, len(C.SWEEP_SCHUBFACH_H) + 1)]
    v = F.gerechnet()
    F.messreihe(C.FAMILIE_SCHUBFACH)
    assert F.gerechnet() == v
    meldungen.clear()
    F.feste_formeln(C.FAMILIE_RAMPEN, 20, 4.5, lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(i, 10) for i in range(1, 11)]


def test_app_zweiter_klick_kommt_aus_dem_zwischenspeicher_und_zeigt_dasselbe():
    F.vergleich.clear()
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    at.radio(key="wachstum_familie").set_value(next(k for k in at.radio(key="wachstum_familie").options if k.startswith("Rampen"))).run(timeout=TIMEOUT)
    at.button(key="wachstum_knopf").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    erste = [d.value.to_dict("records") for d in at.dataframe]
    v = F.gerechnet()
    assert v > 0
    at.button(key="wachstum_knopf").click().run(timeout=TIMEOUT)
    assert not at.exception and F.gerechnet() == v
    assert [d.value.to_dict("records") for d in at.dataframe] == erste
