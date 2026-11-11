"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Formeln der Presets und die festen Formeln der Messreihen."""

import wlt_constants as C
import wlt_evaluation as ev
import wlt_presets as P
import wlt_scenario as S


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert preset["familie"] in C.FAMILIEN
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.DICHTE_MIN <= preset["dichte"] <= C.DICHTE_MAX
        assert C.H_MIN <= preset["h"] <= C.H_MAX and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Handbeispiel F2"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_jeder_regler_ist_fuer_mindestens_eine_familie_aktiv_und_nur_fuer_bekannte_familien():
    assert set(P.AKTIV_FUER) <= set(P.SETTING_SPECS)
    for familien in P.AKTIV_FUER.values():
        assert familien and set(familien) <= set(C.FAMILIEN)


def test_presets_beschreiben_die_gemeinten_formeln():
    f2 = ev.formel_von(ev.Settings(**C.PRESETS["Handbeispiel F2"]))
    assert (f2.n, len(f2.klauseln)) == (5, 6)
    zufall = ev.formel_von(ev.Settings(**C.PRESETS["Zufalls-3-SAT n = 100"]))
    assert (zufall.n, len(zufall.klauseln)) == (100, 426)
    rampen = ev.formel_von(ev.Settings(**C.PRESETS["Rampen (Färbung, n = 60)"]))
    assert rampen.n == 60 * C.RAMPEN
    schubfach = ev.formel_von(ev.Settings(**C.PRESETS["Schubfach h = 6"]))
    assert (schubfach.n, len(schubfach.klauseln)) == (42, 7 + 6 * 21)          # 7 Tauben-Klauseln und je Loch C(7,2) = 21 Paare


def test_messreihe_nutzt_die_festen_formeln():
    assert ev.groessen_der_familie(C.FAMILIE_ZUFALL) == C.SWEEP_ZUFALL_N
    assert len(C.SWEEP_SEEDS) == 10 and len(set(C.SWEEP_SEEDS)) == 10
    formeln = ev.formeln_der_familie(C.FAMILIE_ZUFALL, 40)
    assert [f.name for f in formeln] == [f"Zufalls-3-SAT n = 40, m = 170, Zufalls-Seed {s}" for s in C.SWEEP_SEEDS]
    assert len(ev.formeln_der_familie(C.FAMILIE_SCHUBFACH, 5)) == 1


def test_formeln_sind_deterministisch_und_verschiedene_seeds_geben_verschiedene_formeln():
    a = S.make_formel(C.FAMILIE_ZUFALL, 30, 4.26, seed=1)
    assert a == S.make_formel(C.FAMILIE_ZUFALL, 30, 4.26, seed=1) and a != S.make_formel(C.FAMILIE_ZUFALL, 30, 4.26, seed=2)
    assert S.make_formel(C.FAMILIE_RAMPEN, 30, 4.5, seed=1) != S.make_formel(C.FAMILIE_RAMPEN, 30, 4.5, seed=2)


def test_schreibweise_der_literale_und_klauseln():
    assert S.lit_text(3) == "x3" and S.lit_text(-3) == "¬x3"
    assert S.klausel_text((-1, 2, 3), (-1, 2)) == "[¬x1] ∨ [x2] ∨ x3"
    assert S.wert_text(None) == "frei" and S.wert_text(True) == "w" and S.wert_text(False) == "f"
