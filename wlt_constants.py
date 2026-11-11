"""Konstanten: Regler-Grenzen, Familien der Formeln, feste Zufalls-Seeds, Farben und Presets."""

FAMILIE_F2 = "Handbeispiel F2"
FAMILIE_RAMPEN = "Rampen (Färbung)"
FAMILIE_ZUFALL = "Zufalls-3-SAT"
FAMILIE_SCHUBFACH = "Schubfach"
FAMILIEN = (FAMILIE_F2, FAMILIE_RAMPEN, FAMILIE_ZUFALL, FAMILIE_SCHUBFACH)

N_MIN, N_MAX, DEFAULT_N = 20, 120, 100          # Variablen (Zufalls-3-SAT) bzw. Aufträge (Rampen)
DICHTE_MIN, DICHTE_MAX, DEFAULT_DICHTE = 2.0, 6.0, 4.26   # Klauseln je Variable (Zufall) bzw. mittlerer Grad des Konfliktgraphen (Rampen)
H_MIN, H_MAX, DEFAULT_H = 3, 6, 6               # Schubfach: h + 1 Tauben, h Löcher; h = 7 nur vorgerechnet
SEED_MAX, DEFAULT_SEED = 999999, 7000
RAMPEN = 3                                      # Zahl der Rampen (Farben)
BUDGET = 20000                                  # Konfliktbudget jeder Suche; ein Lauf, der es erreicht, wird als Abbruch ausgewiesen

# Feste Formeln für alle Messreihen: nie ein einzelner Seed als Befund (SplitMix64, Seeds 7000 bis 7009)
SWEEP_SEEDS = tuple(range(7000, 7010))
SWEEP_ZUFALL_N = (40, 60, 80, 100, 120)         # m/n = 4,26
SWEEP_RAMPEN_N = (20, 40, 60, 80, 100)          # mittlerer Grad 4,5
RAMPEN_GRAD = 4.5
SWEEP_SCHUBFACH_H = (3, 4, 5, 6)
SCHUBFACH_VORGERECHNET = 7                      # h = 7 braucht mit dem naiven Verfahren rund drei bis fünf Minuten: Datei wlt_messreihen.json
PROBEN_FIXPUNKT = 200                           # Zahl der zufälligen Entscheidungsfolgen der Fixpunkt-Probe
MESSREIHEN_DATEI = "wlt_messreihen.json"

# Handbeispiel F2 (von Hand nachgerechnet): sechs 3-Klauseln über x1 bis x5
F2_KLAUSELN = ((-1, 2, 3), (-1, -2, 4), (-2, -4, 5), (1, 3, -5), (-3, 4, 5), (-4, -5, 2))
F2_N = 5
F2_ENTSCHEIDUNGEN = (1, 2)
KLEINE_FORMEL_N, KLEINE_FORMEL_M = 8, 28        # zweite Formel der Handpropagation (Zufalls-3-SAT, Zufalls-Seed der Seitenleiste)
SCHRITTANSICHT_MAX_N, SCHRITTANSICHT_MAX_KLAUSELN = 12, 40

COLOR_NAIV = "#c0504d"
COLOR_WATCH = "#2F6B65"
COLOR_LINE = "#4c78a8"
ERGEBNIS_FARBEN = {"erfuellt": "#2F6B65", "beobachter": "#4c78a8", "einheit": "#e0a030", "konflikt": "#c0504d", "ohne_wirkung": "#9a9a9a"}
ERGEBNIS_NAMEN = {"erfuellt": "Klausel schon erfüllt", "beobachter": "Beobachter wandert", "einheit": "Einheit (erzwingt ein Literal)",
                  "konflikt": "Konflikt", "ohne_wirkung": "ohne Wirkung (nur naiv)"}

PRESETS = {
    "Handbeispiel F2": {"familie": FAMILIE_F2, "n": DEFAULT_N, "dichte": DEFAULT_DICHTE, "h": DEFAULT_H, "seed": DEFAULT_SEED},
    "Rampen (Färbung, n = 60)": {"familie": FAMILIE_RAMPEN, "n": 60, "dichte": RAMPEN_GRAD, "h": DEFAULT_H, "seed": DEFAULT_SEED},
    "Zufalls-3-SAT n = 100": {"familie": FAMILIE_ZUFALL, "n": 100, "dichte": DEFAULT_DICHTE, "h": DEFAULT_H, "seed": DEFAULT_SEED},
    "Schubfach h = 6": {"familie": FAMILIE_SCHUBFACH, "n": DEFAULT_N, "dichte": DEFAULT_DICHTE, "h": 6, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Handbeispiel F2": "Sechs Klauseln über fünf Variablen, von Hand nachgerechnet: dieselbe Antwort, 8 gegen 7 Besuche, 22 gegen 13 Lesezugriffe.",
    "Rampen (Färbung, n = 60)": "60 Aufträge auf 3 Rampen, mittlerer Grad 4,5: kurze ursprüngliche Klauseln (Länge 2 und 3), der Vorsprung ist klein.",
    "Zufalls-3-SAT n = 100": "100 Variablen, 426 Klauseln (m/n = 4,26), Zufalls-Seed 7000: die Standardformel der Messreihen.",
    "Schubfach h = 6": "7 Tauben, 6 Löcher: unerfüllbar, viele Klauseln, lange „mindestens ein Loch“-Klauseln.",
}
