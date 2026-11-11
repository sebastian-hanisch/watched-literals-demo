"""Kennzahlen, Messreihen und Verdikte. Jedes Verdikt ist eine reine Funktion `verdict_*(...) -> (Art, Text)`; jede Zahl im Text stammt aus der Messung.

Aufwand wird gezählt, nie in Sekunden gemessen: Besuche (angesehene Klauseln) und Lesezugriffe (nach ihrem Wert gefragte Literale)."""

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median

import wlt_algorithm as A
import wlt_constants as C
import wlt_scenario as S

SCHWELLE_DEUTLICH = 2.0      # ab diesem Faktor (Lesezugriffe naiv / Watched) nennt das Verdikt den Vorsprung deutlich
SCHWELLE_KAUM = 1.2          # unterhalb dieses Faktors gibt es kaum einen Unterschied


@dataclass(frozen=True)
class Settings:
    familie: str = C.FAMILIE_F2
    n: int = C.DEFAULT_N
    dichte: float = C.DEFAULT_DICHTE
    h: int = C.DEFAULT_H
    seed: int = C.DEFAULT_SEED


def formel_von(settings: Settings) -> S.Formel:
    return S.make_formel(settings.familie, settings.n, settings.dichte, settings.h, settings.seed)


def de(x: float, stellen: int = 0) -> str:
    """Deutsche Zahlschreibweise: Punkt als Tausendertrenner (ab vier Stellen), Komma als Dezimalzeichen."""
    text = f"{x:,.{stellen}f}"
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


def antwort_text(antwort) -> str:
    return {True: "erfüllbar", False: "unerfüllbar", None: "nicht entschieden (Budget erreicht)"}[antwort]


def faktor(naiv: float, watch: float):
    """Verhältnis naiv / Watched; None, wenn Watched nichts gelesen hat (nichts zu vergleichen)."""
    return None if watch == 0 else naiv / watch


def je_besuch(lauf) -> float:
    return 0.0 if lauf.besuche == 0 else lauf.lesezugriffe / lauf.besuche


def je_propagation(lauf) -> float:
    return 0.0 if lauf.propagationen == 0 else lauf.lesezugriffe / lauf.propagationen


# ---------------------------------------------------------------------------------------------------------------------------------- Messreihen

def je_propagation_summe(summe: dict) -> float:
    """Lesezugriffe je Propagation einer summierten Zeile (0, wenn nichts propagiert wurde)."""
    return 0.0 if summe["propagationen"] == 0 else summe["lesezugriffe"] / summe["propagationen"]


def _summe(laeufe: list) -> dict:
    nach = {k: sum(l.besuche_nach[k] for l in laeufe) for k in C.ERGEBNIS_NAMEN}
    return {"propagationen": sum(l.propagationen for l in laeufe), "besuche": sum(l.besuche for l in laeufe),
            "lesezugriffe": sum(l.lesezugriffe for l in laeufe), "konflikte": sum(l.konflikte for l in laeufe), "besuche_nach": nach}


def zeile(label, groesse, paare: list) -> dict:
    """Eine Zeile der Messreihe aus den Läufen mit beiden Modi je Formel: `paare` = Liste von {"naiv": Lauf, "watch": Lauf}.

    Der Gesamtfaktor ist die Summe der Lesezugriffe naiv durch die Summe bei Watched; das Band (Minimum, Median, Maximum) steht je Formel."""
    naiv, watch = _summe([p["naiv"] for p in paare]), _summe([p["watch"] for p in paare])
    je_formel = [f for f in (faktor(p["naiv"].lesezugriffe, p["watch"].lesezugriffe) for p in paare) if f is not None]
    return {
        "label": label, "groesse": groesse, "formeln": len(paare), "naiv": naiv, "watch": watch,
        "faktor": faktor(naiv["lesezugriffe"], watch["lesezugriffe"]),
        "faktor_je_propagation": faktor(je_propagation_summe(naiv), je_propagation_summe(watch)),
        "faktor_unter_1": sum(1 for f in je_formel if f < 1),
        "faktor_min": min(je_formel, default=None), "faktor_median": median(je_formel) if je_formel else None, "faktor_max": max(je_formel, default=None),
        "abbrueche": sum(1 for p in paare if p["naiv"].antwort is None or p["watch"].antwort is None),
        "antwort_gleich": sum(1 for p in paare if p["naiv"].antwort == p["watch"].antwort),
        "konflikte_abweichend": sum(1 for p in paare if p["naiv"].konflikte != p["watch"].konflikte),
        "erfuellbar": sum(1 for p in paare if p["watch"].antwort is True),
        "vorgerechnet": False,
    }


def formeln_der_familie(familie: str, groesse, seeds=C.SWEEP_SEEDS) -> list:
    """Die festen Formeln einer Zeile der Messreihe."""
    if familie == C.FAMILIE_ZUFALL:
        return [S.make_formel(familie, n=groesse, dichte=C.DEFAULT_DICHTE, seed=s) for s in seeds]
    if familie == C.FAMILIE_RAMPEN:
        return [S.make_formel(familie, n=groesse, dichte=C.RAMPEN_GRAD, seed=s) for s in seeds]
    if familie == C.FAMILIE_SCHUBFACH:
        return [S.make_formel(familie, h=groesse)]
    raise ValueError(f"keine Messreihe für {familie}")


def groessen_der_familie(familie: str) -> tuple:
    return {C.FAMILIE_ZUFALL: C.SWEEP_ZUFALL_N, C.FAMILIE_RAMPEN: C.SWEEP_RAMPEN_N, C.FAMILIE_SCHUBFACH: C.SWEEP_SCHUBFACH_H}[familie]


def groessenname(familie: str) -> str:
    """Die Größe im Dativ für Sätze („bei 40 Variablen“)."""
    return {C.FAMILIE_ZUFALL: "Variablen", C.FAMILIE_RAMPEN: "Aufträgen", C.FAMILIE_SCHUBFACH: "Löchern"}[familie]


def spaltenname(familie: str) -> str:
    """Die Größe als Spalten- und Achsenbeschriftung."""
    return {C.FAMILIE_ZUFALL: "Variablen n", C.FAMILIE_RAMPEN: "Aufträge", C.FAMILIE_SCHUBFACH: "Löcher h"}[familie]


def messreihe(familie: str, groessen=None, seeds=C.SWEEP_SEEDS, budget: int = C.BUDGET) -> list:
    """Eine Zeile je Größe, gemessen über die festen Formeln (SWEEP_SEEDS); beide Modi, gleiche Formel, gleiches Budget."""
    zeilen = []
    for g in (groessen if groessen is not None else groessen_der_familie(familie)):
        paare = [A.vergleiche(f.n, f.klauseln, budget) for f in formeln_der_familie(familie, g, seeds)]
        zeilen.append(zeile(f"{familie}, {spaltenname(familie)} = {g}", g, paare))
    return zeilen


def vorgerechnete_zeilen(pfad: Path | None = None) -> list:
    """Die in `tools/messreihen.py` vorgerechneten Schubfach-Zeilen (h = 7 braucht naiv rund drei bis fünf Minuten): Liste von Zeilen wie `zeile`,
    mit vorgerechnet = True. Fehlt die Datei, ist die Liste leer."""
    pfad = pfad or Path(__file__).resolve().parent / C.MESSREIHEN_DATEI
    if not pfad.exists():
        return []
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    zeilen = daten["schubfach"]
    for z in zeilen:
        z["vorgerechnet"] = True
    return zeilen


def messreihe_schubfach_mit_vorgerechnet(h_vorgerechnet=C.SCHUBFACH_VORGERECHNET) -> list:
    """Schubfach h = 3 bis 6 live gemessen, dazu die vorgerechnete Zeile h = 7 (falls die Datei sie enthält)."""
    zeilen = messreihe(C.FAMILIE_SCHUBFACH)
    zeilen += [z for z in vorgerechnete_zeilen() if z["groesse"] == h_vorgerechnet]
    return zeilen


FAELLE_BESUCH = (
    ("Zufalls-3-SAT n = 100", C.FAMILIE_ZUFALL, 100),
    ("Rampen n = 60", C.FAMILIE_RAMPEN, 60),
    ("Schubfach h = 5", C.FAMILIE_SCHUBFACH, 5),
    ("Schubfach h = 6", C.FAMILIE_SCHUBFACH, 6),
)


def besuch_faelle(budget: int = C.BUDGET) -> list:
    """Zeilen für Experiment 4: Besuche nach Ergebnis in den Fällen von FAELLE_BESUCH."""
    return [messreihe(familie, [g], budget=budget)[0] | {"label": name} for name, familie, g in FAELLE_BESUCH]


# ---------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_kernfrage(naiv, watch) -> tuple[str, str]:
    """Kernfrage: wie viele Literale liest das naive Verfahren im Vergleich zu Watched? `naiv`, `watch`: Läufe (`A.Lauf`) derselben Formel."""
    if naiv.antwort is None or watch.antwort is None:
        return "warning", (f"Das Budget von {de(C.BUDGET)} Konflikten ist erreicht (naiv: {antwort_text(naiv.antwort)}; Watched: {antwort_text(watch.antwort)}); "
                           f"die Lesezugriffe ({de(naiv.lesezugriffe)} gegen {de(watch.lesezugriffe)}) sind untere Schranken, einen Faktor nennt die Demo hier nicht.")
    if naiv.antwort != watch.antwort:
        return "error", f"Die Antworten weichen ab (naiv: {antwort_text(naiv.antwort)}, Watched: {antwort_text(watch.antwort)}): das darf nicht vorkommen."
    f = faktor(naiv.lesezugriffe, watch.lesezugriffe)
    if f is None:
        return "info", "Hier muss nichts propagiert werden: Watched hat kein Literal gelesen, es gibt keinen Faktor."
    antwort = antwort_text(naiv.antwort)
    zahlen = f"{de(naiv.lesezugriffe)} gegen {de(watch.lesezugriffe)} Lesezugriffe"
    # Die beiden Suchen gehen verschiedene Wege (Propagationen und Konflikte weichen ab): je Propagation gerechnet ist der Vergleich weniger vom Weg abhängig.
    prop = ""
    if naiv.propagationen and watch.propagationen:
        prop = (f" Je Propagation sind es {de(je_propagation(naiv), 1)} gegen {de(je_propagation(watch), 1)} Lesezugriffe "
                f"({de(naiv.propagationen)} gegen {de(watch.propagationen)} Propagationen).")
    if f >= SCHWELLE_DEUTLICH:
        return "success", f"Beide Verfahren sagen: {antwort}. Das naive Verfahren liest **{de(f, 1)}-mal** so viele Literale wie Watched ({zahlen}).{prop}"
    if f >= SCHWELLE_KAUM:
        return "info", f"Beide Verfahren sagen: {antwort}. Das naive Verfahren liest nur **{de(f, 1)}-mal** so viele Literale wie Watched ({zahlen}).{prop}"
    return "warning", f"Beide Verfahren sagen: {antwort}. Kaum ein Unterschied: Faktor **{de(f, 1)}** ({zahlen}).{prop}"


def verdict_wachstum(zeilen: list, groessenname_: str) -> tuple[str, str]:
    """Experiment Wachstum: Faktor der ersten und der letzten Größe, ob er in jedem Schritt wächst, und woraus er sich zusammensetzt (Besuche, Literale je Besuch)."""
    ok = [z for z in zeilen if z["faktor"] is not None]
    if len(ok) < 2:
        return "info", "Für diesen Vergleich fehlen Zeilen mit Propagation."
    erste, letzte = ok[0], ok[-1]
    besuche = faktor(letzte["naiv"]["besuche"], letzte["watch"]["besuche"])
    je_naiv = letzte["naiv"]["lesezugriffe"] / letzte["naiv"]["besuche"]
    je_watch = letzte["watch"]["lesezugriffe"] / letzte["watch"]["besuche"]
    steigt = all(b["faktor"] > a["faktor"] for a, b in zip(ok, ok[1:]))
    verlauf = "wächst in jedem Schritt" if steigt else "wächst nicht in jedem Schritt"
    kind = "success" if letzte["faktor"] >= SCHWELLE_DEUTLICH else "info"
    if letzte["formeln"] > 1 and letzte["faktor_min"] is not None:
        band = f" Je Formel liegt er bei der größten Größe zwischen {de(letzte['faktor_min'], 1)} und {de(letzte['faktor_max'], 1)}"
        band += f" (in {letzte['faktor_unter_1']} von {letzte['formeln']} Formeln unter 1)." if letzte["faktor_unter_1"] else "."
    else:
        band = ""
    return kind, (
        f"Bei {de(erste['groesse'])} {groessenname_} liest das naive Verfahren **{de(erste['faktor'], 1)}-mal** so viele Literale wie Watched, "
        f"bei {de(letzte['groesse'])} **{de(letzte['faktor'], 1)}-mal**; der Faktor {verlauf}.{band} Je Propagation sind es bei der größten Größe "
        f"{de(je_propagation_summe(letzte['naiv']), 1)} gegen {de(je_propagation_summe(letzte['watch']), 1)} Literale. Der Gesamtfaktor setzt sich dort zusammen aus "
        f"{de(besuche, 1)}-mal so vielen Besuchen und {de(je_naiv, 1)} gegen {de(je_watch, 1)} gelesenen Literalen je Besuch."
    )


def verdict_gleiche_antwort(zeilen_paare: list, probe: dict) -> tuple[str, str]:
    """Experiment gleiche Antwort, andere Zahl. `zeilen_paare`: Liste von {"naiv": Lauf, "watch": Lauf} (feste Formeln), `probe`: Ergebnis von `A.fixpunkt_probe`."""
    m = len(zeilen_paare)
    gleich = sum(1 for p in zeilen_paare if p["naiv"].antwort == p["watch"].antwort)
    abweichend = [p for p in zeilen_paare if p["naiv"].konflikte != p["watch"].konflikte]
    fix = f"Der Fixpunkt der Propagation ist in {probe['gleich']} von {probe['proben']} zufälligen Entscheidungsfolgen gleich."
    if gleich < m or probe["gleich"] < probe["proben"]:
        return "error", f"Die Verfahren weichen ab: gleiche Antwort in {gleich} von {m} Formeln. {fix}"
    if not abweichend:
        return "info", (f"Gleiche Antwort in {gleich} von {m} Formeln, und hier auch gleiche Konfliktzahlen. {fix} "
                        "Das ist kein Gesetz: die Reihenfolge der Schlüsse darf abweichen.")
    p = abweichend[0]
    return "info", (f"Gleiche Antwort in {gleich} von {m} Formeln, aber die Konfliktzahl weicht in {len(abweichend)} von {m} ab "
                    f"(erste abweichende Formel: {de(p['naiv'].konflikte)} gegen {de(p['watch'].konflikte)} Konflikte, naiv gegen Watched). {fix} "
                    "Gleichheit der Antwort prüfen, nicht der Zahl.")


def verdict_besuch(zeile_: dict) -> tuple[str, str]:
    """Experiment Besuch (eine Zeile): Anteil der Besuche, die bei Watched nur ein Literal lesen (Klausel schon erfüllt), und der Besuche, die etwas bewirken."""
    w = zeile_["watch"]
    if w["besuche"] == 0:
        return "info", "Hier gab es keinen Besuch."
    nach = w["besuche_nach"]
    erfuellt = nach["erfuellt"] / w["besuche"]
    wirkung = (nach["einheit"] + nach["konflikt"]) / w["besuche"]
    naiv = zeile_["naiv"]
    ohne = f" Beim naiven Verfahren lassen {de(100 * naiv['besuche_nach']['ohne_wirkung'] / naiv['besuche'], 1)} % der {de(naiv['besuche'])} Besuche die Klausel offen und bewirken nichts." if naiv["besuche"] else ""
    return "info", (f"{zeile_['label']}: Bei Watched liest {de(100 * erfuellt, 1)} % der Besuche genau ein Literal (die Klausel ist schon erfüllt), "
                    f"{de(100 * nach['beobachter'] / w['besuche'], 1)} % verschieben einen Beobachter, {de(100 * wirkung, 1)} % erzwingen ein Literal oder melden einen Konflikt "
                    f"({de(w['besuche'])} Besuche).{ohne}")
