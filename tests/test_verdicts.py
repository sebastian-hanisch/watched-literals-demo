"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Läufe und Zeilen, nicht Seeds."""

import wlt_algorithm as A
import wlt_evaluation as ev

NULL_NACH = {"erfuellt": 0, "beobachter": 0, "einheit": 0, "konflikt": 0, "ohne_wirkung": 0}


def lauf(lesen, antwort=True, konflikte=10, besuche=100, props=50, nach=None):
    return A.Lauf(antwort, props, besuche, lesen, konflikte, nach or dict(NULL_NACH), True if antwort else None)


def summe(lesen, besuche, props, konflikte=0, nach=None):
    return {"propagationen": props, "besuche": besuche, "lesezugriffe": lesen, "konflikte": konflikte, "besuche_nach": nach or dict(NULL_NACH)}


def zeile(groesse, naiv, watch, **kw):
    z = {"label": f"Zeile {groesse}", "groesse": groesse, "formeln": 10, "naiv": naiv, "watch": watch, "faktor": ev.faktor(naiv["lesezugriffe"], watch["lesezugriffe"]),
         "faktor_min": 1.5, "faktor_median": 3.0, "faktor_max": 9.0, "faktor_unter_1": 0, "vorgerechnet": False}
    z.update(kw)
    return z


# ------------------------------------------------------------------------------------------------------------------------------ Kernfrage

def test_kernfrage_deutlicher_vorsprung_nennt_faktor_und_beide_zahlen():
    kind, text = ev.verdict_kernfrage(lauf(12345), lauf(1000))                      # 12,345-mal
    assert kind == "success"
    assert "erfüllbar" in text and "**12,3-mal**" in text and "(12.345 gegen 1.000 Lesezugriffe)" in text
    assert "Je Propagation sind es 246,9 gegen 20,0 Lesezugriffe (50 gegen 50 Propagationen)." in text       # 12345 / 50 und 1000 / 50


def test_kernfrage_schwellen_sind_inklusive():
    assert ev.verdict_kernfrage(lauf(200), lauf(100))[0] == "success"              # genau 2,0
    kind, text = ev.verdict_kernfrage(lauf(199), lauf(100))                        # 1,99
    assert kind == "info" and "nur **2,0-mal**" in text
    assert ev.verdict_kernfrage(lauf(120), lauf(100))[0] == "info"                 # genau 1,2
    kind, text = ev.verdict_kernfrage(lauf(119), lauf(100))
    assert kind == "warning" and "Kaum ein Unterschied" in text and "**1,2**" in text


def test_kernfrage_unerfuellbar_budget_und_abweichung():
    assert "unerfüllbar" in ev.verdict_kernfrage(lauf(500, antwort=False), lauf(100, antwort=False))[1]
    kind, text = ev.verdict_kernfrage(lauf(500, antwort=None), lauf(100, antwort=None))
    assert kind == "warning" and "Budget von 20.000 Konflikten" in text and "500 gegen 100" in text
    kind, text = ev.verdict_kernfrage(lauf(500, antwort=True), lauf(100, antwort=False))
    assert kind == "error" and "erfüllbar" in text and "unerfüllbar" in text
    kind, _ = ev.verdict_kernfrage(lauf(0), lauf(0))
    assert kind == "info"                                                           # Watched hat nichts gelesen: kein Faktor


# ------------------------------------------------------------------------------------------------------------------------------ Wachstum

def test_wachstum_nennt_erste_und_letzte_groesse_zerlegung_und_band():
    z1 = zeile(40, summe(250, 100, 50), summe(100, 80, 50))                         # 2,5
    z2 = zeile(120, summe(9000, 3000, 100), summe(1000, 500, 100), faktor_min=0.8, faktor_max=20.0, faktor_unter_1=2)   # 9,0; 6-mal Besuche; 3,0 gegen 2,0 je Besuch
    kind, text = ev.verdict_wachstum([z1, z2], "Variablen")
    assert kind == "success"
    assert "Bei 40 Variablen" in text and "**2,5-mal**" in text and "bei 120 **9,0-mal**" in text and "wächst in jedem Schritt" in text
    assert "zwischen 0,8 und 20,0 (in 2 von 10 Formeln unter 1)" in text
    assert "90,0 gegen 10,0 Literale" in text                                       # je Propagation: 9000/100 gegen 1000/100
    assert "6,0-mal so vielen Besuchen und 3,0 gegen 2,0 gelesenen Literalen je Besuch" in text


def test_wachstum_nicht_in_jedem_schritt_und_info_bei_kleinem_faktor():
    z1 = zeile(1, summe(300, 100, 50), summe(100, 100, 50))
    z2 = zeile(2, summe(190, 100, 50), summe(100, 100, 50))                         # 1,9 < 3,0 und unter der Schwelle 2,0
    kind, text = ev.verdict_wachstum([z1, z2], "Löchern")
    assert kind == "info" and "wächst nicht in jedem Schritt" in text
    assert "Je Formel liegt er" in text and "unter 1" not in text


def test_wachstum_eine_formel_je_zeile_hat_kein_band():
    z1 = zeile(3, summe(200, 100, 50), summe(100, 80, 50), formeln=1)
    z2 = zeile(4, summe(900, 300, 50), summe(100, 80, 50), formeln=1)
    kind, text = ev.verdict_wachstum([z1, z2], "Löchern")
    assert kind == "success" and "Je Formel" not in text


def test_wachstum_ohne_zwei_zeilen():
    assert ev.verdict_wachstum([zeile(3, summe(200, 100, 50), summe(100, 80, 50))], "Löchern")[0] == "info"


# ------------------------------------------------------------------------------------------------------------------------------ Gleiche Antwort, andere Zahl

def test_gleiche_antwort_andere_konfliktzahl():
    paare = [{"naiv": lauf(10, konflikte=300), "watch": lauf(5, konflikte=250)}, {"naiv": lauf(10, konflikte=40), "watch": lauf(5, konflikte=40)}]
    probe = {"proben": 200, "gleich": 200}
    kind, text = ev.verdict_gleiche_antwort(paare, probe)
    assert kind == "info"
    assert "Gleiche Antwort in 2 von 2 Formeln" in text and "Konfliktzahl weicht in 1 von 2 ab" in text and "300 gegen 250" in text
    assert "in 200 von 200 zufälligen Entscheidungsfolgen gleich" in text and "Gleichheit der Antwort prüfen, nicht der Zahl." in text


def test_gleiche_antwort_gleiche_zahl_und_abweichung():
    paare = [{"naiv": lauf(10, konflikte=7), "watch": lauf(5, konflikte=7)}]
    kind, text = ev.verdict_gleiche_antwort(paare, {"proben": 10, "gleich": 10})
    assert kind == "info" and "auch gleiche Konfliktzahlen" in text
    kind, text = ev.verdict_gleiche_antwort([{"naiv": lauf(10, antwort=True), "watch": lauf(5, antwort=False)}], {"proben": 10, "gleich": 10})
    assert kind == "error" and "gleiche Antwort in 0 von 1" in text
    kind, text = ev.verdict_gleiche_antwort(paare, {"proben": 10, "gleich": 9})
    assert kind == "error" and "in 9 von 10" in text


# ------------------------------------------------------------------------------------------------------------------------------ Besuch

def test_besuch_anteile():
    nach = {"erfuellt": 50, "beobachter": 25, "einheit": 20, "konflikt": 5, "ohne_wirkung": 0}
    nach_naiv = {"erfuellt": 60, "beobachter": 0, "einheit": 10, "konflikt": 5, "ohne_wirkung": 25}
    kind, text = ev.verdict_besuch(zeile(1, summe(10, 100, 5, nach=nach_naiv), summe(130, 100, 50, nach=nach), label="Fall A"))
    assert kind == "info"
    assert text.startswith("Fall A: Bei Watched liest 50,0 % der Besuche genau ein Literal")
    assert "25,0 % verschieben einen Beobachter" in text and "25,0 % erzwingen ein Literal oder melden einen Konflikt (100 Besuche)" in text
    assert "Beim naiven Verfahren lassen 25,0 % der 100 Besuche die Klausel offen und bewirken nichts." in text
    assert ev.verdict_besuch(zeile(1, summe(0, 0, 0), summe(0, 0, 0)))[1] == "Hier gab es keinen Besuch."


def test_zahlschreibweise():
    assert ev.de(1234567) == "1.234.567" and ev.de(0.5, 1) == "0,5" and ev.de(1234.56, 1) == "1.234,6" and ev.de(999) == "999"
