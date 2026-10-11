# Verhältniskennzahlen und Cluster: wer ist die Einheit? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-ratio-metric-demo.streamlit.app/)**

Interaktive Demo zu **Verhältniskennzahlen und der Einheit der Auswertung**. **Achtes Stück der Konzepte-Linie „Experimente
und Wirkungsmessung“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine
Learning). Das Vehikel ist dasselbe wie in den Vorgängern (Standort mit täglicher Nachbestellung, Regel A gegen Regel B,
Servicegrad); neu ist, dass die Messung eine **Zeitreihe je Standort** ist: 56 Tage Nachfrage und Fehlmenge, nicht ein Fenster.

## Kernfrage

Der Servicegrad ist ein Verhältnis aus täglichen Werten. Wie viel Effekt zeigt dieselbe Regel je nachdem, wie das Verhältnis
gebildet wird, und was passiert mit dem Intervall, wenn man Tage oder Wochen als unabhängige Einheiten zählt, obwohl je
Standort zugeteilt wurde?

## Modell und Methodik

- **Kennzahl-Definitionen** (`rat_evaluation.estimands`): Quote der Summen (Σ Fehlmenge / Σ Nachfrage, der betriebliche
  Servicegrad) sowie Mittel der Standort-, der Wochen- und der Tagesquoten. Die wahre Wirkung ist je Definition das Mittel über
  die ganze Population von 1 000 Standorten (Regel B minus Regel A, gleiche Nachfrage).
- **Vorrat** (`generate_precomputed.py`): je Population 1 000 Standorte mit 56 Tagen Nachfrage (Mittel 20, Gamma-Poisson) und
  Fehlmenge je Tag unter Regel A und B (Sicherheitsfaktor 1,0 gegen 1,2 / 1,4 / 1,8). Zwei Populationen: *alle gleich* und
  *dauerhaft verschieden* (wahre Nachfrage-Streuung je Standort 2 bis 12 statt der geplanten 5).
- **Experiment:** n Standorte je Arm, Standorte mit Zurücklegen aus der Population gezogen, 4 bis 8 Wochen; jeder Standort
  liefert nur die zugeteilte Regel.
- **Vier Auswertungen** (`rat_evaluation.analyze`): *naiv (Tage)* = Delta-Methode mit jedem Standort-Tag als Einheit;
  *Delta, Cluster* = dieselbe Quote der Summen mit dem Standort als Einheit; *Standort-Welch* = Welch-Test auf den
  Standort-Quoten; *naiv (Wochen)* = Welch-Test auf allen Standort-Wochen. Intervalle mit t-Quantil.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (3 000 Experimente je Zelle, Fehler der Raten höchstens 0,9 Prozentpunkte).
20 Standorte je Arm und 8 Wochen, wenn nicht anders genannt; Regel B mit Sicherheitsfaktor 1,4 bei „mit Wirkung“.

| Frage | Befund |
|---|---|
| Hängen die Tage eines Standorts zusammen? | **Ja:** Autokorrelation 1. Ordnung der Tagesquoten **0,28** in beiden Populationen. |
| Wie viel Effekt zeigt dieselbe Regel je nach Kennzahl? | Bei Faktor 1,4 (alle gleich): Quote der Summen **3,49**, Standort-Mittel **3,41**, Wochen-Mittel **3,04**, Tages-Mittel **2,41 Prozentpunkte**. Das Tagesmittel zeigt **29 bis 34 %** weniger als die Quote der Summen (alle Faktoren und Populationen). |
| Wie oft meldet die naive Auswertung ohne Wirkung einen Unterschied? | Tage als Einheit: **13,7 %** (alle gleich) und **26,9 %** (dauerhaft verschieden), versprochen sind 5 %. Wochen als Einheit: **6,4 %** und **15,1 %**. |
| Und mit dem Standort als Cluster? | Delta-Methode **5,0 %** und **5,8 %**, Standort-Welch **5,0 %** und **5,3 %**. |
| Wie gut deckt das 95-%-Intervall? | Naiv (Tage) **86,3 %** und **73,1 %**; Cluster **95,0 %** und **94,2 %**. |
| Wie eng ist das naive Intervall? | Standardfehler zu **0,76-fach** (alle gleich) und **0,56-fach** (verschieden); das naive Intervall ist bei gleichen Standorten **26 %** schmaler (3,77 gegen 5,12 Punkte). |
| Hat die naive Auswertung nicht mehr Teststärke? | Mit Wirkung: **95,3 %** gegen **87,1 %** (Cluster) bei gleichen Standorten, **83,0 %** gegen **52,1 %** bei verschiedenen. Der Vorsprung kommt aus der überhöhten Fehlalarmrate, nicht aus mehr Information; das Intervall deckt die Wahrheit nur in **86,2 %** bzw. **74,9 %**. |
| Helfen mehr Standorte oder mehr Wochen? | **Nein.** Fehlalarm der naiven Auswertung (alle gleich) von **12,9 bis 14,1 %** über fünf Kombinationen (10 bis 40 Standorte, 4 oder 8 Wochen); der Cluster-Ansatz bleibt zwischen **4,7 und 5,9 %**. |
| Ist die Schätzung verzerrt? | **Nein.** Verzerrung in allen Zellen unter 0,05 Prozentpunkten; verzerrt ist nur das Maß der Unsicherheit. |
| Wie sicher ist die Delta-Methode bei wenigen Standorten? | Bei **10 Standorten je Arm** mit Normalquantil **6,9 %** (alle gleich) bzw. **6,0 %** (verschieden) Fehlalarm, mit t-Quantil **5,2 %** bzw. **4,0 %**. |

## Befunde und Korrekturen gegenüber dem Plan

- **Mehr Daten heilen den Befund nicht.** Die naive Fehlalarmrate bleibt bei fünf Kombinationen von Standorten und Wochen bei
  12,9 bis 14,1 %. Sie hängt von der Abhängigkeit der Tage ab, nicht von der Zahl der Zeilen.
- **Wochen sind besser als Tage, aber nicht gut.** Sieben Tage addiert nehmen den größten Teil der Serienkorrelation heraus
  (6,4 % gegen 13,7 %), aber nicht den Standort-Anteil: bei dauerhaft verschiedenen Standorten bleiben 15,1 %.
- **Die Definition ist keine Spitzfindigkeit.** Fehlmengen entstehen fast nur an Tagen mit großer Nachfrage (bei Regel A **93 %**
  der Fehlmenge an der oberen Hälfte der Tage, die **69 %** der Nachfrage trägt). In der Quote der Summen zählen diese Tage mit
  ihrer Menge, im Tagesmittel nur je ein Tag. Wer „den Servicegrad“ aus einem Dashboard der Tagesquoten liest, sieht etwa ein
  Drittel weniger Wirkung als der betriebliche Wert aus den Summen.
- **Der Cluster ist zuerst Serienkorrelation, nicht Standort-Eigenheit.** In der Vorab-Messreihe auf dem Bestand-Vehikel
  (Phase 0) war die Korrelation der Tage innerhalb des Standorts praktisch null **zwischen** Standorten (Intraklassen-
  korrelation 0,0001); die Aufblähung kam allein aus der Autokorrelation je Standort. Ein echter Standort-Cluster entsteht erst
  mit einer dauerhaften Standort-Eigenheit; deshalb gibt es die zweite Population.
- **Ehrlich heißt weniger Teststärke.** Das Clustern kostet bei gleichen Standorten 8,2 Punkte (87,1 % statt 95,3 %), bei
  verschiedenen 30,9 Punkte (52,1 % statt 83,0 %): das ist der Preis der Antwort „wie viele unabhängige Einheiten habe ich?“.
- **Default-Seed 35:** ein Experiment, in dem alle vier Auswertungen den Effekt finden (Quote der Summen +3,29 Punkte, Tagesmittel
  +2,04; Cluster-Intervall 4,6 Punkte breit, naives 3,5); wie oft das gutgeht, zeigt die Wiederholung darunter.

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Man weiß, welche Kennzahl gemeint ist** | Die Definition verschiebt den Effekt um bis zu ein Drittel. | (dieses Stück) |
| **Die Einheit der Auswertung ist die Einheit der Zuteilung** | Tage oder Wochen als unabhängige Einheiten zu zählen, macht Intervalle zu schmal. | (dieses Stück) |
| **Zugeteilt wird je Standort und Standorte beeinflussen sich nicht** | Teilen Standorte Kundschaft oder Lager, braucht es Cluster nach Nachbarschaft oder Zeitblöcke. | Interferenz und Switchback |
| **Wenige Cluster genügen** | Bei zehn Standorten je Arm ist das Normalquantil leicht liberal; die Demo nutzt das t-Quantil. | (dieses Stück) |
| **Ein Test, eine Kennzahl** | Vier Kennzahlen auf denselben Daten sind selbst vier Tests. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Es gibt eine Vorperiode** | Mit ihr lässt sich die Standort-Streuung herausrechnen. | Varianzreduktion (CUPED) |

Die Zahlen gelten für dieses erfundene Vehikel; in einem Betrieb sind Serienkorrelation und Standort-Unterschiede anders groß.

## Bezug zu OR

Jede Betriebskennzahl ist ein Verhältnis (Servicegrad, Auslastung, Pünktlichkeit), und jede Messung ist eine Zeitreihe je
Standort. Wer ein Pilotexperiment auswertet, muss wissen, welche Einheit zugeteilt wurde und welche Quote berichtet wird, sonst
sind sowohl die Wirkung als auch ihre Unsicherheit eine andere als die, die beschlossen werden soll.

## Verwandte Demos im Portfolio

- [ab-test-demo](https://github.com/sebastian-hanisch/ab-test-demo), [test-power-demo](https://github.com/sebastian-hanisch/test-power-demo):
  Vehikel, Teststärke und Welch-Test.
- [cuped-demo](https://github.com/sebastian-hanisch/cuped-demo): dieselbe dauerhafte Standort-Eigenheit, dort als Vorperiode genutzt.
- [permutation-test-demo](https://github.com/sebastian-hanisch/permutation-test-demo): verteilungsfreie Auswertung und gestörte Fenster.
- [forecast-inventory-demo](https://github.com/sebastian-hanisch/forecast-inventory-demo): die Base-Stock-Regel des Vehikels.

## Verifikation

- **Kennzahlen** (`tests/test_ratio.py`, `tests/test_oracle_ratio_metric.py`): von Hand an einer Mini-Instanz (Nachfrage 100,
  Fehlmenge 6 → 0,94; Tagesmittel 1 − 0,6/7); gegen eine direkte Schleife über Standorte, Wochen und Tage; Mittel der Quoten
  ungleich Quote der Summen bei ungleicher Nachfrage.
- **Delta-Methode:** von Hand (Differenz 0,15, Standardfehler √0,0125, p mit zwei Freiheitsgraden); gegen den Cluster-Bootstrap
  (Standardfehler auf 8 %).
- **Welch** gegen `scipy.stats.ttest_ind` (p-Wert auf 1e-9).
- **Serienkorrelation:** AR(1)-Reihen mit ρ = 0,5 → naive Fehlalarmrate weit über 5 %, Cluster bei 5 %.
- **Vehikel:** Mini-Instanz, Zufall und Test wie im ersten Stück (`tests/test_vehicle.py`, `tests/test_rng.py`).
- **Befunde:** jede Zahl dieses READMEs in `tests/test_claims.py`.
- **Presets, Oberfläche, Footer:** vollständig, Permalink eingerastet, AppTest-Rauchtest, Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: ein Experiment, tausend Wiederholungen, mehr Daten, Grenzen |
| `rat_constants.py` | Vehikel-Konstanten, Populationen, Regler-Grenzen, Presets |
| `rat_rng.py`, `rat_vehicle.py`, `rat_formulas.py`, `rat_stats.py` | Zufall, Standort mit Tagesreihe, exakter Servicegrad, Welch-Test |
| `rat_evaluation.py` | Kennzahl-Definitionen, Ziehung der Experimente, vier Auswertungen, Zusammenfassungen |
| `rat_presets.py`, `rat_visualization.py` | Permalink, Presets; Plotly-Abbildungen (Achsen gesperrt) |
| `generate_precomputed.py`, `precomputed_sites.json` | vorgerechnete Standort-Reihen (2 × 1 000 Standorte) |
| `tools/measure_stueck8.py` | die Messreihe vor dem Text |
| `tests/` | Vehikel, Orakel, Kennzahlen, Presets, Befunde, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Bootstrap über Standorte** und **Permutationstest auf Standort-Ebene:** nicht gebaut (siehe permutation-test-demo für das Prinzip).
- **Gemischte Modelle** (zufälliger Achsenabschnitt je Standort) und **robuste Standardfehler nach Cluster-Anzahl** (CR2, CR3): nicht gebaut.
- **Ungleich große Cluster** (Standorte mit sehr verschiedenem Volumen): in der Population nicht abgebildet.

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

Gebaut mit Streamlit, Plotly, NumPy und SciPy (Verteilungsfunktionen).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html).
