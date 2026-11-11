"""Die kopierten Kern-Module sind unverändert gegenüber der Kern-Version, die im Modulkopf steht (Hash der Datei ohne Kopfzeilen und mit rückübersetzten Importen).

`wlt_rng.py` und `wlt_instanzen.py` sind Kopien von `rng.py` und `instanzen.py`, `wlt_cdcl.py` von `cdcl.py` mit **einer** dokumentierten Abweichung (siehe dessen Kopf):
die Umordnung beim Erzwingen in `_prop_naiv` fehlt. Der Test setzt diese zwei Zeilen wieder ein und vergleicht dann mit dem Kern-Hash."""

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

UMORDNUNG_FEHLT = "                u = offen[0]\n                self._besuch(ci, None, \"einheit\", u)\n"
UMORDNUNG_KERN = ("                u = offen[0]\n                k = c.index(u)\n"
                  "                c[0], c[k] = c[k], c[0]            # erzwungenes Literal an Position 0\n"
                  "                self._besuch(ci, None, \"einheit\", u)\n")


def _kern_text(modul: str) -> tuple[str, str]:
    """(Kern-Version aus dem Kopf, Text im Zustand des Kerns)."""
    text = (ROOT / f"wlt_{modul}.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    version = re.match(r"# Herkunft: Kopie von sat-cp-planung/kern/\w+\.py \(Kern-Version ([0-9a-f]{16})", text).group(1)
    zeilen = text.split("\n")
    i = 0
    while zeilen[i].startswith("#"):
        i += 1
    text = "\n".join(zeilen[i:])
    text = text.replace("from wlt_rng import", "from rng import")
    if modul == "cdcl":
        assert UMORDNUNG_FEHLT in text
        text = text.replace(UMORDNUNG_FEHLT, UMORDNUNG_KERN)
    return version, text


@pytest.mark.parametrize("modul", ["rng", "instanzen", "cdcl"])
def test_kopie_gleicht_der_kern_version(modul):
    version, text = _kern_text(modul)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] == version


def test_kopien_importieren_nichts_aus_dem_kern_oder_anderen_demos():
    for modul in ("rng", "instanzen", "cdcl"):
        quelle = (ROOT / f"wlt_{modul}.py").read_text(encoding="utf-8")
        for zeile in quelle.splitlines():
            if zeile.startswith(("import ", "from ")):
                name = zeile.split()[1]
                assert name in {"heapq", "itertools", "dataclasses", "typing", "wlt_rng"}, (modul, zeile)
