"""Rechnet die Schubfach-Zeilen h = 3 bis 7 vor und schreibt `wlt_messreihen.json` (Aufruf: `python tools/messreihen.py`, aus dem Repo-Ordner).

Warum vorgerechnet: Schubfach h = 7 braucht mit dem naiven Verfahren rund 840 Millionen Lesezugriffe (rund drei bis fünf Minuten Rechenzeit); die App rechnet live nur h = 3
bis 6 und lädt h = 7 aus dieser Datei, ausdrücklich als „vorgerechnet, nicht live“ gekennzeichnet. Die Rechnung ist deterministisch (keine Zufallsformel, keine
Zeitmessung); `tests/test_claims.py` vergleicht die Zeilen h = 3 bis 6 mit einer Neumessung und h = 7 (Watched) ebenfalls; die naive Zeile h = 7 prüft
`WLT_LANGSAM=1 pytest tests/test_claims.py -k vorgerechnet`."""

import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

import wlt_constants as C  # noqa: E402
import wlt_evaluation as ev  # noqa: E402


def main() -> None:
    zeilen = ev.messreihe(C.FAMILIE_SCHUBFACH, [3, 4, 5, 6, 7])
    daten = {
        "hinweis": "vorgerechnet mit tools/messreihen.py, nicht live; Schubfach h Löcher, h + 1 Tauben, naiv gegen Watched, gleiche Suche, Budget siehe unten",
        "budget": C.BUDGET,
        "schubfach": zeilen,
    }
    (HIER / C.MESSREIHEN_DATEI).write_text(json.dumps(daten, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for z in zeilen:
        print(z["label"], z["naiv"]["lesezugriffe"], z["watch"]["lesezugriffe"], round(z["faktor"], 2), z["naiv"]["konflikte"], z["watch"]["konflikte"], flush=True)


if __name__ == "__main__":
    main()
