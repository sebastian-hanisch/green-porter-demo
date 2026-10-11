# Preiskriege im Gleichgewicht: Green und Porter – Streamlit-Demo

<!-- Nach dem Deploy direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-green-porter-demo.streamlit.app/)** -->

Siebtes Stück der **Wiederholte-Spiele-Linie** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Nachfolger von [rauschen-kooperation-demo](https://sebastianhanisch-rauschen-kooperation-demo.streamlit.app/) (Fehler bei der Ausführung) und
[folk-theorem-demo](https://sebastianhanisch-folk-theorem-demo.streamlit.app/) (was Wiederholung tragen kann). Die Kante ist ein `fix`: dort wurde jede Aktion beobachtet,
hier **nur der verrauschte Marktpreis**, nicht die Menge des anderen.

Vehikel: zwei Spediteure wählen jede Woche ihre Kapazität auf einer Relation (Cournot-Duopol, lineare Nachfrage 10 − Q, Kosten 1 je Einheit, multiplikativer lognormaler Preisschock).
Eigennutz und Rationalität sind Modellannahmen.

## Warum dieses Problem

Ein niedriger Preis kann schwache Nachfrage sein oder Überproduktion des anderen. Wer das nicht unterscheiden kann, braucht eine Regel: unter einem Trigger-Preis ein Preiskrieg über T
Perioden. Das macht die Absprache stabil, **aber der Preiskrieg kommt auch dann, wenn niemand abgewichen ist**. Die Demo rechnet exakt, wie oft, wie lang und was das kostet.

## Modell

Absprache bei Gesamtmenge Qc (je Anbieter Qc/2, zwischen Monopol 4,5 und Cournot 6,0); fällt der Preis unter p̄, T Perioden Cournot (3 je Anbieter), dann zurück. Die
Auslösewahrscheinlichkeit α bei Absprache ist **keine freie Wahl**: die abgesprochene Menge muss die beste Antwort sein (Bedingung erster Ordnung in α, global geprüft). Werte V
(Absprache) und W (Kriegsbeginn) aus einem linearen System; der Zeitanteil im Krieg ist αT/(1 + αT).

## Methodik

- **Werte:** `phase_values`: V = π_m + δ[(1−α)V + αW], W = π_c(1−δ^T)/(1−δ) + δ^T V.
- **Abweichung:** `deviation_curve`: V_d(q) für jede Menge q einer Firma bei bleibender Absprache der anderen.
- **Gleichgewicht:** `equilibria`: Nullstellen der FOC (feine Suche plus Bisektion), danach global gegen alle Mengen geprüft.
- **Vorgerechnet:** `gpo_data.json`: bestes Gleichgewicht je (δ, σ) über Qc und T (`tools/precompute.py`).

## Befunde (gemessen, keine Behauptungen)

A = 10, c = 1: Cournot 9,00 je Firma, Monopol 10,125.

| Frage | Befund | Test |
|---|---|---|
| Gibt es Preiskriege auf dem Gleichgewichtspfad? | Ja: bei δ = 0,90, σ = 0,10, Qc = 5,3, T = 30 löst der Trigger mit α = 4,9 % je Absprache-Periode aus, ohne dass jemand abweicht; im Mittel 59 % der Zeit Krieg. | `test_default_equilibria`, `test_simulated_war_share_converges_to_the_formula` |
| Wie viele Gleichgewichte? | Typisch **zwei**: ein ruhiges (α = 4,9 %, Wert 9,57 je Periode) und ein kriegerisches (α = 53 %, Wert 9,14, 94 % Krieg). | `test_default_equilibria` |
| Was bringt die Absprache? | Etwa die Hälfte (50 %) des Abstands zwischen Cournot und Monopol: 9,57 diskontiert je Periode, langfristig im Mittel 9,33 (die Kriege kosten). | `test_default_analysis` |
| Enger absprechen? | Bei Menge 4,8 statt 5,3: α = 13,7 %, 80 % der Zeit Krieg, Wert 9,50; bringt kaum mehr. Mit sehr geduldigen Anbietern (δ = 0,97) trägt Menge 5,0 bei α = 2,4 % (42 % Krieg, Wert 9,68). | `test_tighter_collusion_needs_more_wars`, `test_very_patient_firms_sustain_a_tighter_collusion_with_fewer_triggers` |
| Wann trägt nichts? | Bei kurzer Strafe (T = 3), geringer Geduld (δ = 0,70) oder starkem Rauschen (σ = 0,50) gibt es bei Qc = 5,3 keine tragbare Absprache; im besten Fall der Tabelle liegt der Wert bei 9,07 bis 9,90. | `test_no_equilibrium_presets`, `test_collusion_disappears_with_noise_and_impatience_in_the_table` |
| Zu träger oder zu empfindlicher Trigger? | Zu träge (α = 0,4 α*): es lohnt, mehr zu fahren. Zu empfindlich (α = 2,5 α*): es lohnt, weniger zu fahren, um nicht auszulösen. Nur die FOC-Nullstellen machen die abgesprochene Menge zur besten Antwort. | `test_a_too_sluggish_trigger_invites_overproduction_and_a_too_sensitive_one_invites_underproduction` |

### Befunde gegenüber dem Plan

Der Plan erwartete eine **freie** Trigger-Schwelle („zu enge Schwelle = zu viele Kriege, zu weite = Anreiz zur Abweichung“). Der erste Bau mit freiem α war falsch: Ein Gleichgewicht
legt α fest (zwei Nullstellen), und die „zu enge“ und „zu weite“ Einstellung zeigen sich nur als Abweichungen in **beide** Richtungen. Außerdem zeigte die Vormessung, dass das beste
Gleichgewicht fast immer die längste Strafphase wählt (T = 40 in der Tabelle) und dann die meiste Zeit im Krieg verbringt; und dass ein nach oben **begrenzter** Preisschock
die Preiskriege ganz vermeiden würde (Trigger am Rand der Verteilung), weshalb hier ein lognormaler Schock mit vollem Träger gewählt ist.

## Ehrliche Grenzen

- **Zwei Anbieter, lineare Nachfrage, gleiche Kosten:** mit anderen Strukturen ändern sich die Zahlen, nicht die Logik.
- **Einfache Trigger-Preis-Form:** die optimalen symmetrischen Gleichgewichte (Abreu/Pearce/Stacchetti 1986) haben eine andere, einfachere Struktur mit zwei Mengen und können mehr tragen.
- **Preisschock unabhängig und lognormal:** korrelierte Schocks verändern die Kriegshäufigkeit.
- **Gleichgewicht, keine Vorhersage:** immer Cournot ist ebenfalls eines.
- **Kein Rechtsurteil:** das Modell zeigt eine selbsttragende Absprache ohne Kommunikation, keine kartellrechtliche Einordnung.

## Verifikation

- **Kern:** je Einheit eine Handrechnung (Gewinne, Verteilung des Schocks, Werte und ihre Rekursionen, Trigger-Preis als Quantil, Abweichungskurve an der abgesprochenen Menge, FOC gegen die
  numerische Ableitung, Gleichgewichte und Nicht-Existenz, Simulation).
- **Orakel** (`tests/test_oracle_green_porter.py`): (1) Werte aus der expliziten Markov-Kette über (Absprache, Krieg mit k verbleibenden Perioden); (2) Zeitanteil im Krieg aus der
  Dauerverteilung dieser Kette; (3) der Wert einer Abweichung per Monte-Carlo-Simulation von 60000 Pfaden mit Schock, Trigger und Krieg; (4) die globale Bedingung auf einem Raster von
  4000 Mengen und dass Einstellungen neben den Nullstellen verletzt sind; (5) die FOC-Nullstellen als Nullstellen der zentralen Differenz von V_d.
- **Claims:** jede Zahl dieses READMEs in `tests/test_claims.py`, einschließlich Neuberechnung von drei Zellen der vorgerechneten Tabelle.
- **Oberfläche:** AppTest (jeder Button, jeder Regler am Minimum und Maximum, Permalink begrenzt, Fall ohne Gleichgewicht warnt, Phasen erklärt) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `gpo_algorithm.py` | Kern: Schockverteilung, Werte, Abweichungskurve, FOC, Gleichgewichte, Simulation |
| `gpo_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `gpo_data.json` | Vorgerechnet: bestes Gleichgewicht je (δ, σ) |
| `gpo_evaluation.py` | Analyse, FOC-Kurve, Abweichungskurven, Tabelle, Verdikt |
| `gpo_presets.py` | Permalink (Begrenzen), Presets |
| `gpo_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tools/precompute.py` | Rechnet `gpo_data.json` neu |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handrechnung, Orakel, Claims, Presets, AppTest-Smoke-Test, Footer |

## Bewusst nicht umgesetzt

- **Mehr als zwei Anbieter, asymmetrische Kosten:** eigene Modelle.
- **Optimale (bang-bang-)Gleichgewichte nach Abreu/Pearce/Stacchetti:** eigenes Verfahren; hier nur die einfache Trigger-Preis-Form.
- **Preisschocks mit Gedächtnis (Konjunktur):** andere Kettenstruktur.

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

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
