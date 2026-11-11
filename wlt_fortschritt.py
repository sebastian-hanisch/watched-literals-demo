"""Messreihe und Vergleich mit Fortschrittsanzeige und Zwischenspeicher (nur Bedienung, keine Rechnung).

Aufgabe ist hier eine Formel: `vergleich` ruft `wlt_algorithm.vergleiche` (die ganze Suche in beiden Modi) auf und wird je Formel zwischengespeichert
(`st.cache_data`, höchstens 200 Einträge: die 50 Formeln der Messreihe Zufall, dazu Rampen, Schubfach und die Formeln der Seitenleiste). Messreihe und
Vergleich der Seitenleiste teilen sich diesen Speicher: dieselbe Formel mit demselben Budget wird nur einmal gerechnet. Der Fortschrittsbalken zählt die
fertigen Formeln. Das Ergebnis ist gleich dem der ungepufferten Funktionen aus `wlt_evaluation` (`tests/test_fortschritt.py`)."""

from contextlib import contextmanager

import streamlit as st

import wlt_algorithm as A
import wlt_constants as C
import wlt_evaluation as ev
import wlt_scenario as S

_ZAEHLER = {"gerechnet": 0}


def gerechnet() -> int:
    """Wie viele Formeln in diesem Prozess tatsächlich gerechnet (nicht aus dem Zwischenspeicher geholt) wurden; dient dem Test."""
    return _ZAEHLER["gerechnet"]


@st.cache_data(show_spinner=False, max_entries=200)
def vergleich(n: int, klauseln: tuple, budget: int) -> dict:
    """Die ganze Suche in beiden Modi, gleich `A.vergleiche(n, klauseln, budget)`."""
    _ZAEHLER["gerechnet"] += 1
    return A.vergleiche(n, klauseln, budget)


def _zaehlend(melde, gesamt: int):
    """`vergleich` mit Meldung nach jeder Formel; `melde(fertig, gesamt)` darf None sein."""
    fertig = [0]

    def f(n, klauseln, budget):
        r = vergleich(n, klauseln, budget)
        fertig[0] += 1
        if melde:
            melde(fertig[0], gesamt)
        return r
    return f


def messreihe(familie: str, melde=None) -> list:
    """Die Messreihe der Familie wie die ungepufferte Fassung (`ev.messreihe`, beim Schubfach mit der vorgerechneten Zeile h = 7)."""
    gesamt = sum(len(ev.formeln_der_familie(familie, g)) for g in ev.groessen_der_familie(familie))
    f = _zaehlend(melde, gesamt)
    if familie == C.FAMILIE_SCHUBFACH:
        return ev.messreihe_schubfach_mit_vorgerechnet(vergleich=f)
    return ev.messreihe(familie, vergleich=f)


def feste_formeln(familie: str, n: int, dichte: float, melde=None) -> list:
    """Die festen Formeln der Größe aus der Seitenleiste (Zufall und Rampen: zehn, sonst eine) in beiden Modi: Liste (Name, Vergleich)."""
    if familie in (C.FAMILIE_ZUFALL, C.FAMILIE_RAMPEN):
        formeln = [S.make_formel(familie, n=n, dichte=dichte, seed=s) for s in C.SWEEP_SEEDS]
    else:
        formeln = [S.make_formel(familie, n=n, dichte=dichte)]
    f = _zaehlend(melde, len(formeln))
    return [(x.name, f(x.n, x.klauseln, C.BUDGET)) for x in formeln]


@contextmanager
def fortschrittsbalken(text: str):
    """Fortschrittsbalken mit Beschriftung; liefert `melde(fertig, gesamt)` und räumt den Balken am Ende weg."""
    balken = st.progress(0.0, text=text)

    def melde(fertig: int, gesamt: int) -> None:
        balken.progress(fertig / gesamt, text=f"{text}: {fertig} von {gesamt}")

    try:
        yield melde
    finally:
        balken.empty()
