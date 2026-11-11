# Watched Literals – gleiche Antwort, weniger Klauseln anfassen – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-watched-literals-demo.streamlit.app/)**

Zweites Stück der Linie **SAT und Constraint Programming** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **eine technische Frage** an wachsenden Formeln: Das erste Stück der Linie lässt den SAT-Löser aus Konflikten lernen; **darunter** liegt die Propagation, die nach jeder Entscheidung die Folgerungen zieht. Diese Demo ändert nur sie: dieselbe Suche, einmal **naiv** (jede Klausel ansehen, in der ein Literal falsch wurde) und einmal mit **zwei beobachteten Literalen je Klausel** (Watched Literals, Technik des SAT-Lösers Chaff). Gezählt werden **Besuche** (angesehene Klauseln) und **Lesezugriffe** (nach ihrem Wert gefragte Literale), nie Sekunden. Vehikel sind Zufalls-3-SAT als Wachstumsmaß, die Färbung des Konfliktgraphen von Aufträgen auf Rampen (die Einkleidung der Linie) und das Schubfach als Grenzfall.

## Warum dieses Problem

Ein SAT-Löser muss nach jeder Entscheidung die Folgerungen ziehen. Chaff (Moskewicz u. a. 2001) nennt für diesen Teil, die Constraint-Propagation, etwa 80 % der Laufzeit (eigene Messung der Autoren, hier nur zitiert, nicht nachgemessen). Die Technik der zwei beobachteten Literale spart dort Arbeit, **ohne die Antwort zu ändern**. Die Demo beantwortet drei Fragen mit Zählungen: **Wie viele Literale liest das naive Verfahren im Vergleich?** (je nach Familie und Größe der Formelmenge Gesamtfaktoren von 1,7 bis 47, bei einzelnen Zufallsformeln auch unter 1), **wächst der Vorsprung mit der Formel?** (bei Schubfach und Rampen in jedem Schritt, bei Zufallsformeln nicht in jedem) und **bleibt die Zahl der Konflikte gleich?** (nein: in den meisten gemessenen Zellen weicht die Konfliktzahl ab, gleich ist nur die Antwort). Der letzte Punkt ist eine Lehre für jeden Vergleich zweier Varianten desselben Verfahrens: Gleichheit der Antwort prüfen, nicht der Zahl.

## Modell

- **Formel.** Eine Formel in konjunktiver Normalform: Variablen $x_1, \dots, x_n$, Klauseln aus Literalen. Das Handbeispiel F2 hat fünf Variablen und sechs Klauseln der Länge 3, von Hand nachgerechnet. Zufalls-3-SAT zieht Klauseln über den ganzzahligen SplitMix64 (auf jeder Plattform dieselben Formeln); Rampen-Färbung: Aufträge mit überlappenden Zeitfenstern dürfen nicht dieselbe von 3 Rampen bekommen (Konfliktgraph mit mittlerem Grad 4,5); Schubfach: h + 1 Tauben in h Löchern, unerfüllbar.
- **Propagation.** Wird ein Literal wahr, wird sein Gegenteil falsch. **Naiv:** jede Klausel, die das falsche Literal enthält, wird angesehen; ihre Literale werden in Klauselreihenfolge gelesen, bis ein wahres kommt (Klausel erfüllt); bleibt genau ein freies Literal, wird es erzwungen (**Einheit**), bleibt keines, ist die Klausel im **Konflikt**. **Watched:** jede Klausel beobachtet zwei nicht falsche Literale (anfangs die ersten zwei); angesehen wird sie nur, wenn eines davon falsch wird: erst das andere beobachtete Literal lesen (wahr: fertig), sonst ab Position 3 ein nicht falsches suchen (gefunden: der Beobachter wandert), sonst Einheit oder Konflikt.
- **Zählweise (in beiden Modi dieselbe).** Besuch = eine Klausel wird angesehen, weil ein Literal von ihr falsch wurde; Lesezugriff = ein Literal einer Klausel wird nach seinem Wert gefragt. Die ganze Suche ist ein kleiner CDCL (Konfliktlernen, Aktivität, Neustarts, Standardeinstellungen, Konfliktbudget 20.000); nur die Propagation wechselt. Das naive Verfahren liest in Klauselreihenfolge: eine andere Lesereihenfolge ändert die Zahlen.
- Mathematik, Lesehilfe und Zerlegung des Faktors: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| Propagation, Suche, Zähler | `wlt_cdcl.py` | **Kopie** des Kern-Pakets der Linie (Kern-Version 832b2c10dfdea62d) mit **einer** Abweichung: Der Kern ordnet beim Erzwingen einer Einheit die Klausel um; die Kopie lässt das weg (siehe „Befunde und Korrekturen“). `tests/test_copies.py` prüft den Hash mit eingesetzter Umordnung |
| SplitMix64 | `wlt_rng.py` | Kopie (Kern-Version 5d5d8f45d0e1eddf), nie Python-`random` |
| Formelerzeuger | `wlt_instanzen.py` | Kopie (Kern-Version 6795de796b66fff8): Zufalls-3-SAT, Schubfach, Rampen-Färbung |
| Einzelschritt-Ansicht, ganze Suche in zwei Modi, Fixpunkt-Probe | `wlt_algorithm.py` | `handpropagation` (jeder Besuch mit gelesenen Literalen und Beobachtern), `vergleiche`, `fixpunkt_probe` |
| Formeln und Schreibweise | `wlt_scenario.py` | Handbeispiel F2, Zufall, Rampen, Schubfach |
| Messreihen und Verdikte | `wlt_evaluation.py` | alle Verdikte als reine Funktionen; die Zahl in jedem Text stammt aus der Messung |
| Vorgerechnete Zeile Schubfach h = 7 | `wlt_messreihen.json`, `tools/messreihen.py` | **vorgerechnet, nicht live**: das naive Verfahren liest dort gut 840 Millionen Literale (rund drei bis fünf Minuten Rechenzeit) |

Experimente in der App: **Eine Propagation von Hand** (zwei Spalten, naiv und Watched, jeder Besuch mit gelesenen Literalen, Beobachtern vorher und nachher und Ergebnis), **Wachstum mit der Formel** (Messreihe je Familie), **Gleiche Antwort, andere Zahl** (zehn feste Formeln und 200 Entscheidungsfolgen) und **Was tut ein Besuch?** (Besuche nach Ergebnis); die drei Messreihen laufen auf Knopfdruck. Schnellstart und allgemeine Einstellungen stehen in der Seitenleiste.

## Befunde (gemessen, keine Behauptungen)

Messreihen: Zufall und Rampen zehn feste Formeln je Größe (Zufalls-Seeds 7000 bis 7009), Schubfach eine feste Formel je h, ganze Suche in beiden Modi, gleiche Formel, Budget 20.000 Konflikte (nie erreicht, 0 Abbrüche in allen Zellen). Der **Gesamtfaktor** ist die Summe der Lesezugriffe naiv durch die Summe bei Watched; er mischt zwei Effekte, den Vorsprung je Propagation und den Unterschied zwischen den Wegen der beiden Suchen (Propagationen und Konflikte weichen ab). Je Propagation gerechnet ist der Vergleich weniger vom Weg abhängig; beide Zahlen stehen unten. Die Zählungen sind ganzzahlig und auf jeder Plattform dieselben, die Tests prüfen sie exakt.

| Frage | Befund | Test |
|---|---|---|
| **Handbeispiel F2** (Entscheidungen x1, dann x2) | Naiv 8 Besuche und 22 Lesezugriffe, Watched 7 Besuche und 13 Lesezugriffe; derselbe Fixpunkt (x1, x2, x4, x5 wahr, x3 frei). Watched sieht K4 und K5 nie an, naiv nur K5 nicht. | `test_f2_naiv_von_hand`, `test_f2_watched_von_hand`, `test_claim_handbeispiel_f2` |
| **Zufalls-3-SAT** (m/n = 4,26), Gesamtfaktor bei n = 40 / 60 / 80 / 100 / 120 | 2,5 / 2,7 / 4,2 / 4,0 / 8,9 (Lesezugriffe naiv 61.634 / 231.675 / 592.882 / 2.632.463 / 25.913.527, Watched 24.741 / 86.079 / 142.176 / 655.877 / 2.895.814). Der Faktor wächst **nicht in jedem Schritt** (n = 100 liegt unter n = 80). Erfüllbar 7 / 7 / 7 / 6 / 5 von 10 Formeln. | `test_claim_zufall_messreihe`, `test_claim_zufall_faktor_waechst_nicht_in_jedem_schritt_aber_je_propagation_naiv_in_jedem` |
| **Zufalls-3-SAT, je Propagation** | Naiv 17,9 / 22,6 / 27,3 / 44,9 / 108,8 Lesezugriffe, Watched 7,4 / 7,8 / 7,9 / 9,3 / 13,0; beide Reihen wachsen in jedem Schritt, die naive auf das 6,1-Fache (n = 40 gegen n = 120), die von Watched auf das 1,7-Fache (ungerundet 1,75). | dieselben |
| **Streuung je Formel** (Zufall, n = 100) | Der Faktor liegt je Formel zwischen 0,20 und 14,4; **in 2 von 10 Formeln liest Watched mehr als naiv** (Zufalls-Seed 7003: naiv 84, Watched 257 Konflikte; 7009: naiv 39, Watched 438), weil die Suche in diesen Formeln mit Watched viel mehr Propagationen braucht (7003: naiv 2.079, Watched 6.059; 7009: naiv 1.120, Watched 10.776). Je Propagation liest Watched in allen zehn Formeln weniger (kleinster Faktor 1,9). | `test_claim_zufall_n100_band_je_formel_und_zwei_formeln_unter_eins` |
| **Rampen-Färbung** (60 Aufträge und andere Größen, 3 Rampen, mittlerer Grad 4,5), Gesamtfaktor bei 20 / 40 / 60 / 80 / 100 Aufträgen | 1,8 / 1,9 / 2,0 / 2,4 / 2,8, in jedem Schritt wachsend; Watched liest je Propagation 2,7 bis 3,2 Literale (naiv 4,9 bis 8,9); erfüllbar 1 / 2 / 5 / 2 / 4 von 10; in keiner der 50 Formeln liest Watched mehr. Die ursprünglichen Klauseln sind kurz (Länge 2 und 3); der Vorsprung ist klein, vermutlich deshalb (für die Rampen nicht einzeln gemessen). | `test_claim_rampen_messreihe`, `test_claim_rampen_faktor_waechst_in_jedem_schritt_und_bleibt_unter_dem_zufall_bei_gleichem_aufwand` |
| **Schubfach** (h + 1 Tauben, h Löcher, unerfüllbar), Gesamtfaktor bei h = 3 / 4 / 5 / 6 / 7 | 1,7 / 1,9 / 4,8 / 10,7 / **47,1**, in jedem Schritt wachsend (h = 6: 8.065.528 gegen 755.871 Lesezugriffe; h = 7: 842.295.340 gegen 17.895.735, **vorgerechnet, nicht live**). Je Propagation bei h = 7: 7.566,8 gegen 281,1 Literale, also der Faktor 26,9; der Rest des Gesamtfaktors kommt daher, dass Watched mit 63.653 gegen 111.315 Propagationen einen kürzeren Weg nimmt. | `test_claim_schubfach_live`, `test_claim_schubfach_h7_vorgerechnet_zahlen`, `test_claim_schubfach_faktor_waechst_in_jedem_schritt_von_h3_bis_h7` |
| **Woher der Faktor kommt** (Schubfach h = 7) | 120.843.892 Besuche naiv gegen 6.504.952 bei Watched (das 18,6-fache) und 7,0 gegen 2,8 gelesene Literale je Besuch (das 2,5-fache): 18,6 × 2,5 ≈ 47,1. Der Faktor 47 lässt sich rechnerisch so zerlegen; beide Faktoren hängen an langen Klauseln: In einer Nachzählung am Schubfach h = 6 (nicht Teil der Tests) gelten 98 % der naiven Besuche Klauseln der Länge 7 und mehr, und Watched spart Besuche nur an Klauseln ab Länge 3. | `test_claim_schubfach_h7_vorgerechnet_zahlen` |
| **Vorgerechnete Zeilen** | Die Zeilen h = 3 bis 6 der Datei `wlt_messreihen.json` stimmen mit der Neumessung überein; Watched bei h = 7 ebenfalls. Die naive Zeile h = 7 prüft `WLT_LANGSAM=1 pytest -k vorgerechnet` (rund drei bis fünf Minuten), sie gehört nicht zur Standardsuite. | `test_claim_schubfach_vorgerechnete_zeilen_gleichen_der_neumessung_fuer_h3_bis_h6`, `test_claim_schubfach_h7_watched_live_gleicht_der_vorgerechneten_zeile`, `test_claim_schubfach_h7_naiv_vorgerechnet_gleicht_der_neumessung` |
| **Gleiche Antwort, andere Zahl** | Die Antwort (erfüllbar oder unerfüllbar) ist in allen 104 live gemessenen Formeln gleich (50 Zufall, 50 Rampen, 4 Schubfach) und in der vorgerechneten Zeile Schubfach h = 7. Die **Konfliktzahl weicht ab** in 8 / 10 / 9 / 9 / 10 von 10 Zufallsformeln (n = 40 bis 120), in 0 / 0 / 2 / 4 / 3 von 10 Rampen-Formeln und beim Schubfach bei h = 5 (160 gegen 159), h = 6 (1.057 gegen 1.004) und h = 7 (8.433 gegen 4.811). | `test_claim_zufall_messreihe`, `test_claim_rampen_messreihe`, `test_claim_schubfach_live`, `test_claim_antwort_gleich_in_allen_zellen_der_messreihen` |
| **Gleicher Fixpunkt** | In je 200 zufälligen Entscheidungsfolgen (1 bis 6 Entscheidungen) erreichen beide Verfahren denselben Fixpunkt oder beide einen Konflikt: Handbeispiel F2 (Konflikt in beiden: 9 von 200), Zufall n = 100, Zufalls-Seed 7000 (0), Rampen 60 Aufträge, Zufalls-Seed 7000 (12), Schubfach h = 6 (2): 200 von 200 in jeder Familie. | `test_claim_fixpunkt_probe_200_von_200_in_vier_familien`, `test_fixpunkt_beider_modi_gleicht_der_einfachsten_definition` |
| **Was tut ein Besuch?** | Bei Watched liest 34,8 / 34,3 / 46,0 / 55,5 % der Besuche genau ein Literal (Klausel schon erfüllt) bei Zufall n = 100 (zehn Formeln) / Rampen 60 Aufträge (zehn Formeln) / Schubfach h = 5 / h = 6. Beim naiven Verfahren lassen 28,7 / 18,7 / 16,9 / 9,4 % der Besuche die Klausel offen und bewirken nichts. | `test_claim_besuche_nach_ergebnis`, `test_claim_ein_erfuellt_besuch_liest_bei_watched_genau_ein_literal` |

## Ehrliche Grenzen

- **Lesezugriffe sind eine Zählgröße, keine Zeit.** Was ein Lesezugriff in Python oder in C kostet, sagt die Demo nicht; die 80 % von Chaff sind deren Messung, nicht meine.
- **Der Faktor gilt für diese Lesereihenfolge.** Das naive Verfahren liest in Klauselreihenfolge, bis ein wahres Literal kommt. Die Umordnung des Kerns beim Erzwingen (siehe unten) ändert die naiven Zahlen je nach Formel in beide Richtungen; eine andere Wahl (etwa Literale nach Zufall) ändert sie ebenfalls.
- **Vier Formelfamilien, jeweils wenige Größen.** Zufall n = 40 bis 120 bei m/n = 4,26, Rampen mit 20 bis 100 Aufträgen bei Grad 4,5, Schubfach h = 3 bis 7, Handbeispiel. Zehn Formeln je Größe: der Gesamtfaktor eines Zufallsfalls hängt an wenigen Formeln (n = 100: 2 von 10 unter 1, eine bei 14,4). Über Industrieformeln oder andere Zufallsdichten sagen die Zahlen nichts.
- **Der Gesamtfaktor enthält den Unterschied der Wege.** Watched und naiv gehen in der ganzen Suche verschiedene Wege (andere Propagationen, andere Konfliktzahlen). Wer den Vorsprung der Technik allein will, nimmt die Zahlen je Propagation; sie sind kleiner als der Gesamtfaktor bei Schubfach h = 7 (26,9 gegen 47,1) und größer bei Zufall n = 100 (4,8 gegen 4,0).
- **Der Klauselbestand wächst durch Lernen und bleibt.** Das Löschen gelernter Klauseln ändert die Beobachterlisten und damit die Zahlen; es kommt in dieser Demo nicht vor.
- **Die Fixpunkt-Probe ist eine Stichprobe** (200 Entscheidungsfolgen je Familie, höchstens 6 Entscheidungen), kein Beweis; die Gleichheit der Fixpunkte folgt aus der Definition der Einheitspropagation (jeder Fixpunkt ist derselbe, die Reihenfolge der Schlüsse ändert ihn nicht), und `tests/test_oracle_watched_literals.py` prüft sie zusätzlich auf 200 Formeln gegen eine unabhängige Propagation.
- **Schubfach h = 7 ist vorgerechnet.** Die App rechnet live h = 3 bis 6; die Zeile h = 7 stammt aus `wlt_messreihen.json`, ausdrücklich so gekennzeichnet.
- **Rechenzeit der App.** Die Seitenleiste rechnet eine Formel in beiden Modi (Größenordnung eine bis wenige Sekunden an den Reglerrändern); die Messreihen brauchen Sekunden bis etwa eine halbe Minute und laufen deshalb auf Knopfdruck, mit Fortschrittsbalken (fertige Formeln); jede Formel wird zwischengespeichert, ein erneuter Klick mit gleicher Einstellung antwortet ohne Rechnung (`wlt_fortschritt.py`, ohne Änderung der Rechnung; Messreihe und Vergleich teilen den Speicher). Zeiten sind kein Befund.

## Befunde und Korrekturen gegenüber dem Plan

- **Zufall n = 100: der Gesamtfaktor ist 4,0, nicht 6,0.** Der Plan nannte 6,0 aus einer Vormessung mit anderen Formeln (Python-`random`); die Demo zieht ihre Formeln über SplitMix64, die Zahlen sind überholt. Je Propagation liegt der Vorsprung bei 4,8.
- **Schubfach h = 7: 47,1 statt 49.** Die Plan-Zahl 882.883.926 naive Lesezugriffe ist neu 842.295.340 (Watched unverändert 17.895.735). Der Rohwert der Vormessung lautet 882.884.926 (Tippfehler im Plan); der Unterschied zu 842.295.340 hat die Größe der Wirkung der Umordnung im Kern (siehe nächster Punkt), ist für h = 7 aber nicht nachgemessen.
- **Die Umordnung im Kern ändert die naiven Zahlen.** Der Kern lässt das naive Verfahren beim Erzwingen einer Einheit das erzwungene Literal an den Klauselanfang tauschen; das ändert die Lesereihenfolge späterer Besuche. Mit dieser Umordnung zählt das Handbeispiel F2 20 statt der von Hand gerechneten 22 Lesezugriffe; auf größeren Formeln hat der Unterschied das andere Vorzeichen. Die Kopie `wlt_cdcl.py` lässt die Umordnung weg. Scratch-Messung (nicht im Test): Zufall n = 100 (zehn Formeln) 2.657.771 naive Lesezugriffe mit Umordnung gegen 2.632.463 ohne (+1,0 %), Schubfach h = 6 8.515.486 gegen 8.065.528 (+5,6 %).
- **Die Zerlegung 18,6 × 2,5 sagt nicht, ob die Klausellänge der Grund ist.** Bei Schubfach h = 7 liegt der Faktor 47 rechnerisch zum größeren Teil in der Zahl der Besuche (das 18,6-fache) und zum kleineren in den Lesezugriffen je Besuch (das 2,5-fache). Die Besuchsersparnis entsteht allerdings nur an Klauseln ab Länge 3, und am Schubfach h = 6 gelten 98 % der naiven Besuche Klauseln der Länge 7 und mehr (Nachzählung, nicht Teil der Tests); die Vermutung „weil die Klauseln lang sind“ ist damit nicht widerlegt. Eine Ursache für das Verhältnis ist nicht belegt: gemessen sind die beiden Faktoren, nicht ihr Grund.
- **Lateinische Quadrate fehlen.** Der Plan führte sie nur als Erwartung aus der Vormessung; der Kern hat keinen Erzeuger. Die Demo nimmt statt dessen die Rampen-Färbung und misst sie neu. Ergebnis: der Vorsprung dort ist klein (Faktor 1,8 bis 2,8).
- **Zwei Formeln mit Faktor unter 1.** Der Plan erwartete einen Vorsprung in jeder Zelle; bei Zufall n = 100 liest Watched in 2 von 10 Formeln mehr als naiv (siehe Befunde). Das ist ein Wegeffekt, kein Fehler: die Fixpunkte sind gleich.
- **Schnellstart „Rampen (Färbung, n = 60)“:** Der Plan nannte keine Dichte; die Demo nimmt den mittleren Grad 4,5.

## Bewusst nicht umgesetzt

- **Keine Zeitmessung.** Lesezugriffe und Besuche genügen für die Frage; Sekunden würden Konstanten von Python mit denen von C vermischen.
- **Kein Löschen gelernter Klauseln, keine anderen Lesereihenfolgen, keine Beobachter-Strategien jenseits der zwei ersten Literale.** Das sind eigene Fragen (das Löschen gehört zu einem späteren Stück der Linie).
- **Kein OR-Tools in der App.** CP-SAT dient nur als Gegenprobe im Test (`tests/test_oracle_watched_literals.py`, Antwort gleich in 15 Formeln); es steht in `requirements-dev.txt`.
- **Kein PDF-Export.** Die Demo hat kein Ergebnis, das sich als Bericht lohnt; die Tabellen lassen sich direkt aus der App kopieren.
- **Schubfach h = 8 und größer** (naiv nicht in vertretbarer Rechenzeit): weder live noch vorgerechnet.

## Verifikation

Die Suite hat 146 Tests (`pytest --collect-only -q tests`); einer davon (die naive Zeile Schubfach h = 7, rund drei bis fünf Minuten) läuft nur mit `WLT_LANGSAM=1` und ist sonst übersprungen.

- **Kern:** Handbeispiel F2 Schritt für Schritt von Hand (jeder Besuch, jede gelesene Literalzahl, jeder Beobachter vorher und nachher: `tests/test_algorithm.py`); Mini-Instanz mit Klauseln der Länge 2 von Hand (Watched liest je Besuch genau ein Literal), Klausel der Länge 1 nur über die Suche; Randfälle: doppelte Literale, Tautologie, leere Klausel, leere Formel, leere Entscheidungsfolge, Konflikt gleich nach der ersten Entscheidung, lange Klauseln (Schubfach), Budget (`tests/test_edge_cases.py`).
- **Orakel** (`tests/test_oracle_watched_literals.py`): (1) eine eigene Referenz-Propagation mit der Zählregel des Plans vergleicht Fixpunkt, Konflikt, Besuche, Lesezugriffe und Propagationen auf 200 Zufallsformeln mit Entscheidungsfolgen in beiden Modi; (2) eine einfachste Einheitspropagation ohne Warteschlange und Beobachter vergleicht den Fixpunkt; (3) die naiven Besuche sind die Summe der Vorkommen aller abgearbeiteten Literale; (4) die Antwort der ganzen Suche gegen OR-Tools CP-SAT (Zufall, Schubfach, Rampen, beide Modi, Modell geprüft); dazu Eigenschaften: Invariante der Beobachter nach der Propagation, Lesezugriffe ≥ Besuche und die Lesegrenzen je Besuch (Watched höchstens Länge − 1, naiv höchstens Länge), Umbenennen der Variablen, Beobachter nach dem Zurückspringen und nach dem Lernen.
- **Kopien:** Hash gegen die Kern-Version (`tests/test_copies.py`), Regressionstests der kopierten Einheiten (`tests/test_kern_cdcl.py`, `tests/test_kern_rng_instanzen.py`: SplitMix64-Referenzwerte, Formelgenerator, Konfliktanalyse, Rücksprung, Löschregel, Annahmen, Spur).
- **Verdikte** (`tests/test_verdicts.py`): jede Schwelle und jede Zahl im Text an handgesetzten Zeilen.
- **Zahlen der README** (`tests/test_claims.py`): jede Zahl der Befunde an den festen Formeln, exakt (ganzzahlige Zähler); „Messung dieser README, nicht im Test“ steht nur bei der Scratch-Messung der Umordnung.
- **Schnellstart und Layout:** Schnellstart-Knöpfe vollständig, Werte innerhalb der Reglergrenzen; Schnellstart oben in der Seitenleiste, fester Kopf, aktiver Schnellstart-Knopf hervorgehoben, jede Änderung eines Reglers hebt die Markierung auf, nicht wirksame Regler sind gesperrt (`tests/test_presets.py`, `tests/test_layout.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder wirksame Regler an den Rändern, die drei Messknöpfe, Handpropagation mit jeder Entscheidung, Permalink), Footer-Test, Laufzeit-Importe (`tests/test_app.py`, `tests/test_footer.py`, `tests/test_runtime_imports.py`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Kopf, Ergebnis, Kernfrage, vier Experimente, Grenzen, Mathematik) |
| `requirements-dev.txt` | Laufzeit plus pytest, OR-Tools (nur Gegenprobe) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/messreihen.py` | rechnet die Schubfach-Zeilen h = 3 bis 7 vor und schreibt `wlt_messreihen.json` |
| `wlt_algorithm.py` | Einzelschritt-Ansicht, ganze Suche in zwei Modi, Fixpunkt-Probe |
| `wlt_cdcl.py` | Kopie des CDCL aus dem Kern der Linie (eine dokumentierte Abweichung) |
| `wlt_constants.py` | Regler-Grenzen, Familien, feste Seeds, Farben, Schnellstart |
| `wlt_evaluation.py` | Messreihen, Kennzahlen, Verdikte als reine Funktionen |
| `wlt_instanzen.py` | Kopie der Formelerzeuger |
| `wlt_fortschritt.py` | Fortschrittsbalken und Zwischenspeicher für Messreihe und Vergleich (je Formel; keine eigene Rechnung) |
| `wlt_layout.py` | Fester Kopf (Stylesheet) |
| `wlt_messreihen.json` | vorgerechnete Schubfach-Zeilen (h = 3 bis 7) |
| `wlt_presets.py` | Permalink (Begrenzen), Schnellstart in der Seitenleiste (aktiver Schnellstart-Knopf hervorgehoben), Zufalls-Seed-Knopf, gesperrte Regler je Familie |
| `wlt_rng.py` | Kopie des SplitMix64 |
| `wlt_scenario.py` | Formeln und Schreibweise der Literale |
| `wlt_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Randfälle, Orakel, Kopien, Verdikte, Claims, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und pandas; OR-Tools nur in den Tests.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
