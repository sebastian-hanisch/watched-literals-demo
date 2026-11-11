"""Watched Literals – gleiche Antwort, weniger Klauseln anfassen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zweites Stück der Linie „SAT und Constraint Programming“: dieselbe Propagation mit und ohne beobachtete Literale, gezählt in Besuchen und Lesezugriffen.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import wlt_algorithm as A
import wlt_constants as C
import wlt_evaluation as ev
import wlt_presets as P
import wlt_scenario as S
from wlt_layout import dunkles_design, kopf_css
from wlt_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from wlt_visualization import build_besuch, build_faktor, build_lesezugriffe, build_wachstum

st.set_page_config(page_title="Watched Literals – Sebastian Hanisch", layout="wide")

WACHSTUM_FAMILIEN = {
    "Zufalls-3-SAT (m/n = 4,26, 10 feste Formeln je Größe)": C.FAMILIE_ZUFALL,
    "Rampen-Färbung (mittlerer Grad 4,5, 3 Rampen, 10 feste Formeln je Größe)": C.FAMILIE_RAMPEN,
    "Schubfach (h = 3 bis 6 live, h = 7 vorgerechnet)": C.FAMILIE_SCHUBFACH,
}
HAND_FORMELN = {"Handbeispiel F2 (5 Variablen, 6 Klauseln)": "f2", f"Kleine Zufallsformel ({C.KLEINE_FORMEL_N} Variablen, {C.KLEINE_FORMEL_M} Klauseln)": "klein"}
HAND_VARIABLEN = C.KLEINE_FORMEL_N
ERGEBNIS_KURZ = {"erfuellt": "wahr (Klausel erfüllt)", "beobachter": "Beobachter wandert", "einheit": "Einheit", "konflikt": "Konflikt", "ohne_wirkung": "noch offen"}


@st.cache_data(show_spinner=False)
def _vergleich(n, klauseln):
    return A.vergleiche(n, klauseln)


@st.cache_data(show_spinner=False)
def _hand(n, klauseln, entscheidungen, watch):
    return A.handpropagation(n, klauseln, entscheidungen, watch)


@st.cache_data(show_spinner=False)
def _messreihe(familie):
    if familie == C.FAMILIE_SCHUBFACH:
        return ev.messreihe_schubfach_mit_vorgerechnet()
    return ev.messreihe(familie)


@st.cache_data(show_spinner=False)
def _feste_formeln(familie, n, dichte):
    """Die zehn festen Formeln der Größe aus der Seitenleiste, beide Modi (nur Zufalls-3-SAT und Rampen); sonst die eine Formel."""
    if familie in (C.FAMILIE_ZUFALL, C.FAMILIE_RAMPEN):
        formeln = [S.make_formel(familie, n=n, dichte=dichte, seed=s) for s in C.SWEEP_SEEDS]
    else:
        formeln = [S.make_formel(familie, n=n, dichte=dichte)]
    return [(f.name, A.vergleiche(f.n, f.klauseln)) for f in formeln]


@st.cache_data(show_spinner=False)
def _probe(n, klauseln):
    return A.fixpunkt_probe(n, klauseln)


@st.cache_data(show_spinner=False)
def _besuch_faelle():
    return ev.besuch_faelle()


def _entscheidung_optionen():
    optionen = ["keine"]
    for v in range(1, HAND_VARIABLEN + 1):
        optionen += [f"x{v} = wahr", f"x{v} = falsch"]
    return optionen


def _entscheidung_literal(text):
    if text == "keine":
        return None
    name, _, wert = text.partition(" = ")
    v = int(name[1:])
    return v if wert == "wahr" else -v


def _hand_tabelle(lauf):
    """Schrittliste als Tabelle; beobachtete Literale stehen in eckigen Klammern (Klammer, nicht nur Farbe)."""
    zeilen = []
    for st_ in lauf.schritte:
        beob = set(st_["beobachter_vorher"] or ())
        gelesen = ", ".join(f"{S.lit_text(l)} = {S.wert_text(None if w == 0 else w == 1)}" for l, w in st_["gelesen"])
        if st_["ergebnis"] == "beobachter":
            wirkung = f"wandert auf {S.lit_text(st_['neues_literal'])}"
        elif st_["ergebnis"] == "einheit":
            wirkung = f"Einheit: erzwingt {S.lit_text(st_['neues_literal'])}"
        else:
            wirkung = ERGEBNIS_KURZ[st_["ergebnis"]]
        zeile = {"Nr": st_["nr"], "wahr geworden": S.lit_text(st_["wahr_geworden"]), "falsch geworden": S.lit_text(st_["falsch_geworden"]),
                 "Klausel": f"K{st_['klausel'] + 1}: " + S.klausel_text(st_["literale"], beob)}
        if lauf.watch:
            zeile["Beobachter vorher → nachher"] = (", ".join(S.lit_text(l) for l in st_["beobachter_vorher"]) + " → "
                                                     + ", ".join(S.lit_text(l) for l in st_["beobachter_nachher"]))
        zeile.update({"gelesen (Wert)": gelesen, "Ergebnis": wirkung, "Besuche": st_["besuche"], "Lesezugriffe": st_["lesezugriffe"]})
        zeilen.append(zeile)
    return pd.DataFrame(zeilen)


def _band(z):
    if z["faktor_min"] is None:
        return "–"
    if z["formeln"] == 1:
        return "eine Formel"
    return f"{ev.de(z['faktor_min'], 1)} bis {ev.de(z['faktor_max'], 1)}"


def _wachstum_tabelle(zeilen, groessenname):
    daten = []
    for z in zeilen:
        daten.append({
            groessenname: z["groesse"], "Formeln": z["formeln"], "erfüllbar": z["erfuellbar"],
            "Lesezugriffe naiv": z["naiv"]["lesezugriffe"], "Lesezugriffe Watched": z["watch"]["lesezugriffe"],
            "je Propagation naiv": round(z["naiv"]["lesezugriffe"] / z["naiv"]["propagationen"], 1) if z["naiv"]["propagationen"] else 0.0,
            "je Propagation Watched": round(z["watch"]["lesezugriffe"] / z["watch"]["propagationen"], 1) if z["watch"]["propagationen"] else 0.0,
            "Faktor": round(z["faktor"], 1) if z["faktor"] is not None else None, "Band je Formel": _band(z),
            "Konflikte naiv / Watched": f"{ev.de(z['naiv']['konflikte'])} / {ev.de(z['watch']['konflikte'])}",
            "Herkunft": "vorgerechnet, nicht live" if z["vorgerechnet"] else "live gerechnet",
        })
    return pd.DataFrame(daten)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in wlt_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("👀 Watched Literals – gleiche Antwort, weniger Klauseln anfassen")
st.markdown(
    """
Ein SAT-Löser muss nach **jeder Entscheidung** die Folgerungen ziehen: Wird ein Literal falsch, kann eine Klausel zur **Einheit** werden und ein anderes Literal erzwingen. Das **naive Verfahren**
sieht dafür jede Klausel an, in der ein Literal falsch wurde, und liest ihre Literale der Reihe nach. **Watched Literals** beobachten je Klausel nur **zwei** Literale und sehen eine Klausel erst an, wenn
eines davon falsch wird. Die Demo zählt **Besuche** (angesehene Klauseln) und **Lesezugriffe** (nach ihrem Wert gefragte Literale), nie Sekunden: **gleiche Antwort, in der Summe über die gemessenen Formeln weniger Lesezugriffe, aber nicht dieselbe Konfliktzahl.**

Weiter unten: vier Experimente (**🔬 Eine Propagation von Hand**, **Wachstum mit der Formel**, **Gleiche Antwort, andere Zahl**, **Was tut ein Besuch?**), der Abschnitt **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktionieren Watched Literals", expanded=True):
    st.markdown(
        """
1. **Naiv:** Wird ein Literal falsch, wird **jede Klausel** angesehen, die es enthält. Ihre Literale werden der Reihe nach gelesen, bis ein wahres kommt (dann ist die Klausel erfüllt) oder alle gelesen sind
   (nur ein freies Literal übrig: **Einheit**, es wird erzwungen; keines übrig: **Konflikt**).
2. **Watched:** Jede Klausel beobachtet **zwei nicht falsche Literale** (anfangs die ersten zwei). Wird eines falsch, wird nur diese Klausel angesehen: erst das **andere beobachtete Literal** lesen
   (wahr: fertig), sonst **ab Position 3** ein nicht falsches Literal suchen und den Beobachter dorthin verschieben; findet sich keines, ist die Klausel Einheit oder im Konflikt.
3. **Warum das reicht:** Solange beide beobachteten Literale nicht falsch sind, kann die Klausel nichts erzwingen. Eine Klausel, deren Beobachter nicht betroffen sind, wird nie angefasst. Beim Zurückspringen
   in der Suche brauchen die Beobachter keine Anpassung (nach Moskewicz u. a. 2001, Chaff).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Formel der Ergebnis- und Vergleichsabschnitte**")
    familie = st.selectbox("Familie", C.FAMILIEN, key="familie_select", help="Welche Formel die Abschnitte „Ergebnis“ und „Gleiche Antwort, andere Zahl“ untersuchen.")
    aktiv = lambda key: familie in P.AKTIV_FUER[key]  # noqa: E731
    n = st.slider("Variablen n (Zufall) bzw. Aufträge (Rampen)", *bounds("n_slider"), key="n_slider", disabled=not aktiv("n_slider"),
                  help="Gilt nur für Zufalls-3-SAT und Rampen-Färbung; sonst gesperrt.")
    dichte = st.slider("Klauseln je Variable m/n (Zufall) bzw. mittlerer Grad (Rampen)", *bounds("dichte_slider"), key="dichte_slider", step=0.01,
                       disabled=not aktiv("dichte_slider"), help="Gilt nur für Zufalls-3-SAT (Standard 4,26) und Rampen-Färbung (Standard 4,5); sonst gesperrt.")
    h = st.slider("Löcher h (Schubfach)", *bounds("h_slider"), key="h_slider", disabled=not aktiv("h_slider"),
                  help="Gilt nur für das Schubfach (h + 1 Tauben, h Löcher). h = 7 steht im Experiment „Wachstum“ als vorgerechnete Zeile.")
    seed = st.number_input("Zufalls-Seed der Formel", *bounds("seed_input"), key="seed_input", step=1, disabled=not aktiv("seed_input"),
                           help="Gilt nur für Zufalls-3-SAT und Rampen-Färbung; Handbeispiel und Schubfach sind fest.")
    st.button("🎲 Neue Formel generieren", width="stretch", on_click=randomize_seed, disabled=not aktiv("seed_input"))

sync_query_params({"familie_select": familie, "n_slider": int(n), "dichte_slider": float(dichte), "h_slider": int(h), "seed_input": int(seed)})

settings = ev.Settings(familie, int(n), float(dichte), int(h), int(seed))
formel = ev.formel_von(settings)
with st.spinner("Rechne die Suche mit beiden Verfahren …"):
    vergleich = _vergleich(formel.n, formel.klauseln)
naiv, watch = vergleich["naiv"], vergleich["watch"]

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"Formel: {formel.name}; {formel.n} Variablen, {len(formel.klauseln)} Klauseln. Beide Suchen sind dieselbe CDCL-Suche (Lernen, Aktivität, Neustarts), nur die Propagation unterscheidet sich.")
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
m1.metric("Lesezugriffe naiv", ev.de(naiv.lesezugriffe), delta="Referenz", delta_color="off")
m2.metric("Lesezugriffe Watched", ev.de(watch.lesezugriffe), delta=f"{ev.de(watch.lesezugriffe - naiv.lesezugriffe)} gegen naiv", delta_color="inverse")
f_ges = ev.faktor(naiv.lesezugriffe, watch.lesezugriffe)
m3.metric("Faktor naiv / Watched", "–" if f_ges is None else f"{ev.de(f_ges, 1)}-mal", delta="Lesezugriffe", delta_color="off")
m4.metric("Antwort", ev.antwort_text(watch.antwort) if watch.antwort == naiv.antwort else "abweichend", delta=f"{ev.de(naiv.konflikte)} / {ev.de(watch.konflikte)} Konflikte (naiv / Watched)", delta_color="off")
if settings.familie == C.FAMILIE_F2:
    st.caption("Beim Handbeispiel entscheidet die Suche selbst (nicht x1, x2 wie im Experiment „Eine Propagation von Hand“); deshalb weichen diese Zahlen von denen dort ab.")
st.plotly_chart(build_lesezugriffe(naiv, watch), width="stretch", key="main_chart")
st.caption(f"Besuche: naiv {ev.de(naiv.besuche)}, Watched {ev.de(watch.besuche)}. Propagationen (belegte Literale, die abgearbeitet wurden): naiv {ev.de(naiv.propagationen)}, Watched {ev.de(watch.propagationen)}.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viel weniger liest Watched, und stimmt die Antwort?")
kind, text = ev.verdict_kernfrage(naiv, watch)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1: Eine Propagation von Hand --------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Eine Propagation von Hand")
st.caption("Dieselben Entscheidungen, dieselbe Formel, zwei Spalten: links das naive Verfahren, rechts Watched. Beobachtete Literale stehen in eckigen Klammern. Werte: w (wahr), f (falsch), frei.")
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
hand_name = c1.selectbox("Formel", list(HAND_FORMELN), key="hand_formel")
optionen = _entscheidung_optionen()
d1 = c2.selectbox("Entscheidung 1", optionen, index=optionen.index("x1 = wahr"), key="hand_d1")
d2 = c3.selectbox("Entscheidung 2", optionen, index=optionen.index("x2 = wahr"), key="hand_d2")
d3 = c4.selectbox("Entscheidung 3", optionen, index=0, key="hand_d3")
hand_formel = S.make_formel(C.FAMILIE_F2) if HAND_FORMELN[hand_name] == "f2" else S.kleine_formel(int(seed))
folge = tuple(l for l in (_entscheidung_literal(t) for t in (d1, d2, d3)) if l is not None)
hand = {w: _hand(hand_formel.n, hand_formel.klauseln, folge, w) for w in (False, True)}
st.caption(f"Formel: {hand_formel.name}. " + " ".join(f"K{i + 1} ({S.klausel_text(k)})" for i, k in enumerate(hand_formel.klauseln)))
if HAND_FORMELN[hand_name] == "klein":
    st.caption("Die kleine Zufallsformel folgt dem Zufalls-Seed aus der Seitenleiste.")
ignoriert = [l for l in folge if abs(l) > hand_formel.n]
if ignoriert:
    st.caption("Übersprungen, weil die Variable in dieser Formel fehlt: " + ", ".join(S.lit_text(l) for l in ignoriert) + ".")
spalten = st.columns(2)
for spalte, (w, titel) in zip(spalten, ((False, "Naiv"), (True, "Watched"))):
    lauf = hand[w]
    with spalte:
        st.markdown(f"**{titel}**")
        if lauf.schritte:
            st.dataframe(_hand_tabelle(lauf), hide_index=True, width="stretch")
        else:
            st.info("Kein Besuch: keine der gewählten Entscheidungen macht ein Literal falsch, das eine Klausel enthält oder beobachtet.")
        for art, lit in lauf.log:
            if art == "uebersprungen":
                st.caption(f"{S.lit_text(lit)}: schon belegt, nicht entschieden.")
            elif art == "abbruch":
                st.caption(f"Konflikt nach der Entscheidung {S.lit_text(lit)}: der Lauf endet.")
        nie = ", ".join(f"K{i + 1}" for i in lauf.nie_besucht) or "keine"
        st.metric("Besuche / Lesezugriffe", f"{lauf.besuche} / {lauf.lesezugriffe}", delta=f"nicht angesehene Klauseln: {nie}", delta_color="off")
konflikt_naiv, konflikt_watch = hand[False].konflikt is not None, hand[True].konflikt is not None
if konflikt_naiv and konflikt_watch:
    st.info("Konflikt in beiden Verfahren: ein Konflikt bricht die Propagation ab, die Belegungen davor dürfen abweichen, weil die Reihenfolge der Schlüsse abweicht.")
elif konflikt_naiv != konflikt_watch:
    st.error("Nur ein Verfahren findet einen Konflikt: das darf nicht vorkommen.")
elif hand[False].belegung == hand[True].belegung:
    st.success("Gleicher Fixpunkt: **ja**, dieselben Literale sind belegt.")
else:
    st.error("Die Fixpunkte weichen ab: das darf nicht vorkommen.")
st.markdown(
    "Belegung am Ende: " + (", ".join(f"{S.lit_text(v if w else -v)}" for v, w in sorted(hand[True].belegung.items())) or "keine")
    + f". Besuche naiv gegen Watched: {hand[False].besuche} gegen {hand[True].besuche}; Lesezugriffe: {hand[False].lesezugriffe} gegen {hand[True].lesezugriffe}."
)

st.markdown("---")

# --- Experiment 2: Wachstum mit der Formel ----------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wachstum mit der Formel")
st.caption("Wie ändert sich der Vorsprung mit der Größe? Zehn feste Formeln je Größe (Zufalls-Seeds 7000 bis 7009), die ganze Suche in beiden Modi, Budget "
           f"{ev.de(C.BUDGET)} Konflikte; der Gesamtfaktor ist die Summe der Lesezugriffe naiv durch die Summe bei Watched, das Band zeigt Minimum bis Maximum der Faktoren je Formel.")
wachstum_name = st.radio("Familie der Messreihe", list(WACHSTUM_FAMILIEN), key="wachstum_familie")
wachstum_familie = WACHSTUM_FAMILIEN[wachstum_name]
if st.button("▶️ Messreihe rechnen", key="wachstum_knopf"):
    with st.spinner("Rechne die Messreihe (je Größe zehn Formeln mit beiden Verfahren; wenige Sekunden bis etwa eine halbe Minute) …"):
        st.session_state.setdefault("wachstum", {})[wachstum_familie] = _messreihe(wachstum_familie)
zeilen = st.session_state.get("wachstum", {}).get(wachstum_familie)
if zeilen:
    gname = ev.groessenname(wachstum_familie)
    spalte_gr = ev.spaltenname(wachstum_familie)
    st.dataframe(_wachstum_tabelle(zeilen, spalte_gr), hide_index=True, width="stretch")
    sp1, sp2 = st.columns(2)
    sp1.plotly_chart(build_wachstum(zeilen, spalte_gr), width="stretch", key="wachstum_chart")
    sp2.plotly_chart(build_faktor(zeilen, spalte_gr), width="stretch", key="faktor_chart")
    if any(z["vorgerechnet"] for z in zeilen):
        st.caption("Die Zeile h = 7 ist **vorgerechnet, nicht live** (`wlt_messreihen.json`, erzeugt mit `tools/messreihen.py`): das naive Verfahren liest dort gut 840 Millionen Literale.")
    kind, text = ev.verdict_wachstum(zeilen, gname)
    getattr(st, kind)(text)
else:
    st.info("Noch nicht gerechnet: „Messreihe rechnen“ startet die Reihe für die gewählte Familie.")

st.markdown("---")

# --- Experiment 3: Gleiche Antwort, andere Zahl -----------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Gleiche Antwort, andere Zahl")
st.caption("Beide Verfahren erreichen bei jeder Entscheidungsfolge denselben Fixpunkt, aber sie ziehen die Schlüsse in anderer Reihenfolge, und die ganze Suche geht dadurch einen anderen Weg. "
           "Die Formeln stammen aus der Seitenleiste (Zufall und Rampen: zehn feste Formeln dieser Größe, sonst die eine Formel).")
schluessel3 = (settings.familie, settings.n, settings.dichte, settings.h)
if st.button("▶️ Vergleich rechnen", key="gleich_knopf"):
    with st.spinner("Rechne die Formeln in beiden Modi und die Fixpunkt-Probe (200 zufällige Entscheidungsfolgen) …"):
        paare = _feste_formeln(settings.familie, settings.n, settings.dichte)
        probe = _probe(formel.n, formel.klauseln)
    st.session_state["gleich"] = (schluessel3, paare, probe)
gleich = st.session_state.get("gleich")
if gleich and gleich[0] == schluessel3:
    _, paare, probe = gleich
    tabelle = [{"Formel": name, "Antwort": ev.antwort_text(p["watch"].antwort), "Konflikte naiv": p["naiv"].konflikte, "Konflikte Watched": p["watch"].konflikte,
                "Propagationen naiv": p["naiv"].propagationen, "Propagationen Watched": p["watch"].propagationen,
                "Lesezugriffe naiv": p["naiv"].lesezugriffe, "Lesezugriffe Watched": p["watch"].lesezugriffe} for name, p in paare]
    st.dataframe(pd.DataFrame(tabelle), hide_index=True, width="stretch")
    st.caption(f"Fixpunkt-Probe auf der Formel „{formel.name}“: {probe['proben']} zufällige Entscheidungsfolgen (1 bis 6 Entscheidungen), davon {probe['konflikt_beide']} mit Konflikt in beiden Modi.")
    kind, text = ev.verdict_gleiche_antwort([p for _, p in paare], probe)
    getattr(st, kind)(text)
else:
    st.info("Noch nicht gerechnet: „Vergleich rechnen“ startet die Rechnung für die Formel der Seitenleiste.")

st.markdown("---")

# --- Experiment 4: Was tut ein Besuch? --------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Was tut ein Besuch?")
st.caption("Anteil der Besuche nach Ergebnis in vier Fällen (Zufall und Rampen: zehn feste Formeln, Schubfach: eine Formel). Bei Watched liest ein Besuch mit dem Ergebnis „Klausel schon erfüllt“ genau ein Literal.")
if st.button("▶️ Besuche auswerten", key="besuch_knopf"):
    with st.spinner("Rechne die vier Fälle (wenige Sekunden) …"):
        st.session_state["besuch"] = _besuch_faelle()
faelle = st.session_state.get("besuch")
if faelle:
    st.plotly_chart(build_besuch(faelle), width="stretch", key="besuch_chart")
    for z in faelle:
        kind, text = ev.verdict_besuch(z)
        getattr(st, kind)(text)
else:
    st.info("Noch nicht gerechnet: „Besuche auswerten“ startet die vier Fälle.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Lesezugriffe sind ein Maß für die Arbeit.** | Sie sind eine Zählgröße, keine Zeit: Was ein Lesezugriff kostet, hängt von Sprache, Speicherlayout und Zwischenspeicher ab. Die Demo sagt nichts über Sekunden; die Angabe, dass die Propagation in Chaff den größten Teil der Laufzeit ausmacht (etwa 80 %), ist eine Messung der Chaff-Autoren (Moskewicz u. a. 2001), keine der Demo. |
| **Das naive Verfahren liest in Klauselreihenfolge.** | Eine andere Lesereihenfolge (etwa das zuletzt erzwungene Literal zuerst) ändert die Zahl der Lesezugriffe; der Faktor gilt für diese Wahl. |
| **Vier Formelfamilien.** | Gemessen sind Handbeispiel, Zufalls-3-SAT, Rampen-Färbung und Schubfach, jeweils mit den gezeigten Größen; für andere Familien (zum Beispiel Industrieformeln) sagen die Zahlen nichts. |
| **Der Klauselbestand wächst durch Lernen und bleibt.** | Das Löschen gelernter Klauseln ändert die Beobachterlisten und damit die Zahlen; es ist nicht Teil dieser Demo. |
| **Gleiche Antwort heißt nicht gleiche Zahl.** | Die Konfliktzahl der ganzen Suche unterscheidet sich zwischen den Modi (Experiment „Gleiche Antwort, andere Zahl“); ein Vergleich der Modi braucht gleiche Antworten, nicht gleiche Zahlen. |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist eine Formel $F$ in konjunktiver Normalform, also eine Menge von Klauseln $C$, jede eine Menge von Literalen. Gesucht ist keine Lösung, sondern der Aufwand der
**Einheitspropagation**: wie oft Klauseln angesehen und Literale gelesen werden, bis alle Folgerungen gezogen sind.

| Symbol | Bedeutung |
|---|---|
| $F$ | Formel, Menge von Klauseln $C$ |
| $\alpha$ | Teilbelegung; $\alpha(\ell) \in \{\text{wahr}, \text{falsch}, \text{frei}\}$ für ein Literal $\ell$ |
| $p$ | Literal, das gerade wahr wurde; $\bar p$ ist dann falsch |
| $B_{\text{naiv}}, B_{\text{W}}$ | Zahl der Besuche (angesehene Klauseln) beim naiven Verfahren bzw. mit Beobachtern |
| $L_{\text{naiv}}, L_{\text{W}}$ | Zahl der Lesezugriffe (nach dem Wert gefragte Literale) |

**Einheit und Konflikt.** Eine Klausel $C$ ist unter $\alpha$ eine *Einheit*, wenn kein Literal wahr und genau eines frei ist; dann muss dieses Literal wahr werden. Sind alle Literale falsch, ist $\alpha$ ein *Konflikt*.
Der *Fixpunkt* der Propagation ist die Belegung, die entsteht, wenn man Einheiten erzwingt, bis keine mehr übrig ist (oder ein Konflikt auftritt).

**Naiver Besuch.** Wird $p$ wahr, wird jede Klausel mit $\bar p$ angesehen. Der Besuch liest die Literale in Klauselreihenfolge bis zum ersten wahren Literal:

$$r_{\text{naiv}}(C, \alpha) = \min\{\, i : \alpha(c_i) = \text{wahr} \,\} \quad \text{bzw.} \quad r_{\text{naiv}}(C, \alpha) = |C| \text{ (kein wahres Literal)}.$$

**Besuch mit Beobachtern.** Jede Klausel $C = (c_1, \dots, c_k)$, $k \ge 2$, beobachtet die Literale an den Positionen 1 und 2. Besucht wird sie nur, wenn eines davon falsch wird. Der Besuch liest das andere beobachtete
Literal (ein Lesezugriff); ist es wahr, endet er. Sonst werden die Positionen $3, \dots, k$ gelesen, bis ein nicht falsches Literal gefunden ist (der Beobachter wandert dorthin). Findet sich keines, ist die Klausel
eine Einheit oder im Konflikt:

$$1 \le r_{\text{W}}(C, \alpha) \le |C| - 1, \qquad 1 \le r_{\text{naiv}}(C, \alpha) \le |C|.$$

**Invariante.** Nach einer vollständig abgearbeiteten Propagation ohne Konflikt gilt für jede Klausel: entweder sind beide beobachteten Literale nicht falsch, oder eines ist falsch und das andere wahr. Nur dann
darf die Klausel unangesehen bleiben, ohne dass eine Einheit oder ein Konflikt unentdeckt bleibt. `tests/test_oracle_watched_literals.py` prüft das an Zufallsformeln.

**Zerlegung des Faktors.** Mit $\bar r = L / B$ (Lesezugriffe je Besuch) ist der Gesamtfaktor eine Identität, keine Näherung:

$$\frac{L_{\text{naiv}}}{L_{\text{W}}} = \frac{B_{\text{naiv}}}{B_{\text{W}}} \cdot \frac{\bar r_{\text{naiv}}}{\bar r_{\text{W}}}, \qquad \bar r = \frac{L}{B}.$$

Das Experiment „Wachstum“ nennt beide Faktoren für die größte Größe der Reihe. Die Besuche und Lesezugriffe der beiden Modi stammen aus **derselben** Suche mit **verschiedener** Reihenfolge der Schlüsse, deshalb
sind die Konfliktzahlen und die Zahl der Propagationen beider Läufe nicht gleich; gleich ist nur die Antwort (erfüllbar oder unerfüllbar).

**Literatur.** Moskewicz, Madigan, Zhao, Zhang, Malik: *Chaff: Engineering an Efficient SAT Solver*, Design Automation Conference (DAC) 2001: zwei beobachtete Literale je Klausel, Besuch nur beim Falschwerden eines
beobachteten Literals, keine Anpassung der Beobachter beim Zurückspringen. Die Lesezugriffe als Zählgröße und alle Zahlen dieser Demo sind eigene Messungen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
