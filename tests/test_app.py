"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Button (Presets, Zufalls-Seed,
die vier Messknöpfe), fährt jeden wirksamen Regler an seine Grenzen und prüft, dass kein Python-Fehler auftritt - insbesondere `StreamlitDuplicateElementId`
(mehrere st.plotly_chart ohne eindeutiges key=) und `StreamlitAPIException` bei Slidern. Gesperrte Regler lassen sich auch im AppTest nicht ändern; sie werden
mit dem Preset ihrer Familie freigeschaltet (siehe tests/test_layout.py)."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import wlt_constants as C
import wlt_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "▶"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen; die Messknöpfe tragen ▶️ und werden bewusst geklickt
MESSKNOEPFE = ("wachstum_knopf", "gleich_knopf", "besuch_knopf")


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    knoepfe = [(index, b.label) for index, b in enumerate(_fresh_app().button) if not b.disabled]     # der Zufalls-Seed-Knopf ist beim Handbeispiel gesperrt
    assert len(knoepfe) >= len(C.PRESETS) + len(MESSKNOEPFE), "Presets und Messknöpfe fehlen"
    for index, label in knoepfe:
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_zufalls_seed_knopf_ist_fuer_zufallsformeln_wirksam():
    at = _fresh_app()
    at.sidebar.button(key="preset_Zufalls-3-SAT n = 100").click().run(timeout=TIMEOUT)
    assert not at.sidebar.button[-1].disabled
    alt = at.sidebar.number_input(key="seed_input").value
    at.sidebar.button[-1].click().run(timeout=TIMEOUT)
    assert not at.exception and at.sidebar.number_input(key="seed_input").value != alt


@pytest.mark.parametrize("familie", [C.FAMILIE_ZUFALL, C.FAMILIE_RAMPEN, C.FAMILIE_SCHUBFACH])
def test_every_active_slider_at_its_min_and_max_does_not_raise(familie):
    name = next(n for n, p in C.PRESETS.items() if p["familie"] == familie)
    probe = _fresh_app()
    probe.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    aktiv = [s.key for s in probe.sidebar.slider if not s.disabled]
    assert aktiv, "kein wirksamer Regler"
    for key in aktiv:
        for edge in ("min", "max"):
            at = _fresh_app()
            at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
            slider = at.sidebar.slider(key=key)
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (familie, key, edge, [str(e) for e in at.exception])


def test_die_messknoepfe_rechnen_und_zeigen_ein_verdikt():
    at = _fresh_app()
    for key in MESSKNOEPFE:
        at.button(key=key).click().run(timeout=TIMEOUT)
        assert not at.exception, (key, [str(e) for e in at.exception])
    texte = " ".join(e.value for e in at.success) + " " + " ".join(e.value for e in at.info)
    assert "liest das naive Verfahren" in texte                                    # Wachstum
    assert "Gleiche Antwort in 1 von 1 Formeln" in texte                           # Gleiche Antwort (Handbeispiel F2: eine Formel)
    assert "der Besuche genau ein Literal" in texte                                # Besuch


def test_die_handpropagation_folgt_den_entscheidungen():
    at = _fresh_app()
    assert any("Gleicher Fixpunkt: **ja**" in s.value for s in at.success)
    at.selectbox(key="hand_d3").set_value("x3 = falsch").run(timeout=TIMEOUT)
    assert not at.exception
    at.selectbox(key="hand_formel").set_value(next(o for o in at.selectbox(key="hand_formel").options if o.startswith("Kleine"))).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    for key in ("hand_d1", "hand_d2", "hand_d3"):
        for wahl in at.selectbox(key=key).options:
            at.selectbox(key=key).set_value(wahl).run(timeout=TIMEOUT)
            assert not at.exception, (key, wahl, [str(e) for e in at.exception])


def test_permalink_uebernimmt_familie_und_begrenzt_werte():
    at = AppTest.from_file(APP_PATH)
    at.query_params["fam"] = C.FAMILIE_SCHUBFACH
    at.query_params["h"] = "99"
    at.query_params["n"] = "1"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.selectbox(key="familie_select").value == C.FAMILIE_SCHUBFACH
    assert at.sidebar.slider(key="h_slider").value == C.H_MAX and at.sidebar.slider(key="n_slider").value == C.N_MIN
    at2 = AppTest.from_file(APP_PATH)
    at2.query_params["fam"] = "gibt es nicht"
    at2.run(timeout=TIMEOUT)
    assert at2.sidebar.selectbox(key="familie_select").value == P.SETTING_SPECS["familie_select"].default
