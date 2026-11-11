"""Szenario: die Formeln der Demo (Handbeispiel F2, Rampen-Färbung, Zufalls-3-SAT, Schubfach) und die Schreibweise der Literale.

Eine Formel ist `Formel(n, klauseln, name)`: n Variablen 1..n, Klauseln als Tupel von Literalen (+v wahr, -v falsch). Alle Zufallsformeln laufen über den
ganzzahligen SplitMix64 (`wlt_rng`, über `wlt_instanzen`), nie über Python-`random` oder `hash()`."""

from typing import NamedTuple

import wlt_constants as C
import wlt_instanzen as I


class Formel(NamedTuple):
    n: int
    klauseln: tuple
    name: str


def klauselzahl(familie: str, n: int, dichte: float) -> int:
    """Zahl der Klauseln einer Zufalls-3-SAT-Formel mit Dichte m/n (gerundet)."""
    return int(round(dichte * n))


def make_formel(familie: str, n: int = C.DEFAULT_N, dichte: float = C.DEFAULT_DICHTE, h: int = C.DEFAULT_H, seed: int = C.DEFAULT_SEED) -> Formel:
    """Deterministisch aus den Angaben: gleiche Eingabe, gleiche Formel."""
    if familie == C.FAMILIE_F2:
        return Formel(C.F2_N, tuple(C.F2_KLAUSELN), "Handbeispiel F2")
    if familie == C.FAMILIE_ZUFALL:
        m = klauselzahl(familie, n, dichte)
        inst = I.rand3(n, m, seed)
        return Formel(inst.n, tuple(inst.klauseln), f"Zufalls-3-SAT n = {n}, m = {m}, Zufalls-Seed {seed}")
    if familie == C.FAMILIE_RAMPEN:
        inst = I.rampen_instanz(n, dichte, seed, C.RAMPEN)
        return Formel(inst.n, tuple(inst.klauseln), f"Rampen: {n} Aufträge, {C.RAMPEN} Rampen, Grad {dichte:g}, Zufalls-Seed {seed}")
    if familie == C.FAMILIE_SCHUBFACH:
        inst = I.pigeonhole(h)
        return Formel(inst.n, tuple(inst.klauseln), f"Schubfach h = {h} ({h + 1} Tauben, {h} Löcher)")
    raise ValueError(f"unbekannte Familie: {familie}")


def kleine_formel(seed: int) -> Formel:
    """Kleine Zufallsformel für die Handpropagation (höchstens SCHRITTANSICHT_MAX_N Variablen und SCHRITTANSICHT_MAX_KLAUSELN Klauseln)."""
    inst = I.rand3(C.KLEINE_FORMEL_N, C.KLEINE_FORMEL_M, seed)
    return Formel(inst.n, tuple(inst.klauseln), f"Zufalls-3-SAT n = {C.KLEINE_FORMEL_N}, m = {C.KLEINE_FORMEL_M}, Zufalls-Seed {seed}")


def lit_text(lit: int) -> str:
    """x3 bzw. ¬x3."""
    return f"x{lit}" if lit > 0 else f"¬x{-lit}"


def klausel_text(klausel, beobachter=()) -> str:
    """Klausel als Text; beobachtete Literale stehen in eckigen Klammern (Klammer, nicht nur Farbe)."""
    return " ∨ ".join(f"[{lit_text(l)}]" if l in beobachter else lit_text(l) for l in klausel)


def wert_text(w) -> str:
    """w (wahr), f (falsch) oder frei."""
    return "frei" if w is None else ("w" if w else "f")
