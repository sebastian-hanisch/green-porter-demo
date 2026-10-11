"""Preiskriege im Gleichgewicht: Green und Porter - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der Wiederholte-Spiele-Linie: Zwei Anbieter sehen nur den verrauschten Marktpreis. Eine Absprache mit Trigger-Preis ist ein Gleichgewicht, und
Preiskriege treten darin auf, ohne dass jemand abweicht. Exakt gerechnet: Gleichgewichts-Auslösewahrscheinlichkeit, Werte, Kriegsanteil.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import gpo_constants as C
import gpo_evaluation as E
from gpo_evaluation import PI_COURNOT, PI_MONOPOLY, Settings, fmt
from gpo_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from gpo_visualization import build_deviation, build_foc, build_price_series, build_table

st.set_page_config(page_title="Preiskriege im Gleichgewicht: Green und Porter – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return E.analyse(settings)


@st.cache_data(show_spinner=False)
def _foc(settings):
    return E.foc_curve(settings)


@st.cache_data(show_spinner=False)
def _deviation(settings, alphas):
    return E.deviation_curves(settings, list(alphas))


@st.cache_data(show_spinner=False)
def _table():
    return E.table_matrix()


st.title("⚔️ Preiskriege im Gleichgewicht: Green und Porter")
st.markdown(
    """
Zwei Spediteure bedienen dieselbe Relation und wählen jede Woche ihre **Kapazität**. Der Marktpreis hängt von der Gesamtmenge ab und schwankt zufällig
(Nachfrage, Wetter, Auslastung). Jeder sieht **nur den Preis**, nicht die Menge des anderen. Fällt der Preis, weiß keiner, ob die Nachfrage schwach war oder
der andere mehr gefahren ist.

Ein Gleichgewicht ist dann eine Absprache mit **Trigger-Preis**: halten, solange der Preis über der Schwelle liegt; fällt er darunter, ein Preiskrieg über T Perioden, danach
wieder die Absprache. Das Besondere: **Die Preiskriege kommen im Gleichgewicht vor, ohne dass jemand abgewichen ist.** Sie sind der Preis dafür, dass Abweichen
bestraft werden kann, obwohl man es nicht sieht.

Weiter unten: **❓ Kernfrage**, drei Experimente (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Vorgänger sind
[rauschen-kooperation-demo](https://sebastianhanisch-rauschen-kooperation-demo.streamlit.app/) (Fehler bei der Ausführung) und
[folk-theorem-demo](https://sebastianhanisch-folk-theorem-demo.streamlit.app/) (was Wiederholung tragen kann).
"""
)

with st.expander("So funktioniert die Trigger-Preis-Absprache", expanded=True):
    st.markdown(
        """
1. **Absprache-Phase:** Jeder fährt die abgesprochene Menge (die Hälfte der Gesamtmenge Qc, zwischen Monopol 4,5 und Cournot 6,0).
2. **Beobachtung:** Beide sehen den Marktpreis p = θ · (10 − Q) mit einem zufälligen Schock θ (Erwartung 1).
3. **Trigger:** Liegt p unter dem Trigger-Preis, beginnt ein **Preiskrieg**: T Perioden lang fährt jeder die Cournot-Menge (3), die schlechtere, aber stabile
   Gleichgewichtsmenge ohne Absprache.
4. **Rückkehr:** Nach T Perioden wieder Absprache. Niemand muss „bestraft“ werden, die Drohung allein hält die Absprache zusammen.
5. **Der Trigger ist nicht frei wählbar:** Er muss so liegen, dass die abgesprochene Menge für beide die **beste Antwort** ist. Das legt die Wahrscheinlichkeit α
   fest, mit der er auch ohne Abweichen auslöst.
        """
    )

with st.expander("Die zwei Phasen: wer macht was?", expanded=True):
    st.markdown(
        "| Phase | Menge je Anbieter | Gesamtmenge | erwarteter Gewinn je Anbieter | Übergang |\n|---|---|---|---|---|\n"
        f"| **Absprache** | Qc/2 (Regler) | Qc | (10 − Qc − 1) · Qc/2 | Preis unter Trigger: Krieg beginnt |\n"
        f"| **Preiskrieg** | 3,0 (Cournot) | 6,0 | {fmt(PI_COURNOT)} | nach T Perioden zurück zur Absprache |\n"
        f"| **zum Vergleich: Monopol** | 2,25 | 4,5 | {fmt(PI_MONOPOLY)} | nicht als Gleichgewicht tragbar (Abweichen lohnt) |"
    )
    st.caption("Alle Gewinne sind Erwartungswerte; der Preis schwankt mit lognormalem Schock der Streuung σ (Regler).")

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Markt**")
    sigma = st.slider("Schwankung des Preises σ", *bounds("sigma_slider"), step=C.SIGMA_STEP, key="sigma_slider",
                      help="Streuung des multiplikativen Preisschocks (lognormal, Erwartung 1). Je größer, desto schlechter lässt sich Abweichen vom Zufall unterscheiden.")
    delta = st.slider("Geduld δ", *bounds("delta_slider"), step=C.DELTA_STEP, key="delta_slider", help="Abzinsfaktor je Periode.")
    st.markdown("**Absprache**")
    qc = st.slider("Abgesprochene Gesamtmenge Qc", *bounds("qc_slider"), step=C.QC_STEP, key="qc_slider",
                   help="4,5 ist die Monopolmenge, 6,0 die Cournot-Menge (keine Absprache).")
    t = st.slider("Dauer des Preiskriegs T (Perioden)", *bounds("t_slider"), step=C.T_STEP, key="t_slider", help="Wie lange nach dem Auslösen beide Cournot fahren.")
    seed = st.number_input("Zufalls-Seed der Preisreihe", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Preisreihe würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"delta_slider": round(float(delta), 2), "sigma_slider": round(float(sigma), 2), "qc_slider": round(float(qc), 2), "t_slider": int(t), "seed_input": int(seed)})

settings = Settings(round(float(delta), 2), round(float(sigma), 2), round(float(qc), 2), int(t), int(seed))
an = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎬 Eine Preisreihe im Gleichgewicht")
if an.best is None:
    st.warning("Bei diesen Einstellungen gibt es kein Gleichgewicht mit Absprache: Es bleibt die Cournot-Menge in jeder Periode. Ändern Sie Qc, T, δ oder σ.")
else:
    b = an.best
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Auslösewahrscheinlichkeit α", f"{fmt(b['alpha'] * 100, 1)} %", delta="je Absprache-Periode, ohne Abweichen", delta_color="off")
    m2.metric("Zeitanteil im Krieg", f"{fmt(b['war_share'] * 100, 0)} %", delta=f"Simulation, {an.sim_steps} Perioden ab Absprache: {fmt(an.sim_war_share * 100, 0)} %", delta_color="off")
    m3.metric("Wert je Periode (diskontiert)", fmt(b["per_period_value"]), delta=f"langfristig im Mittel {fmt(b['long_run_profit'])}; Cournot {fmt(PI_COURNOT)}, Monopol {fmt(PI_MONOPOLY)}", delta_color="off")
    m4.metric("Erreichter Anteil der Absprache-Rente", f"{fmt(an.share_of_rent * 100, 0)} %", delta="zwischen Cournot (0 %) und Monopol (100 %)", delta_color="off")
    st.plotly_chart(build_price_series(an.sim), width="stretch", key="price_chart")
    st.caption(f"Simulation über {an.sim_steps} Perioden, beide halten sich an die Strategie. Jedes rote Kreuz ist ein Preiskrieg, den allein der Zufall ausgelöst hat.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Gibt es Preiskriege, obwohl niemand abweicht?")
level, sentence = E.verdict(an, settings)
{"success": st.success, "warning": st.warning, "info": st.info}[level](sentence)
st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Warum ist die abgesprochene Menge die beste Antwort?")
if an.best is None:
    st.info("Ohne Gleichgewicht gibt es nichts zu prüfen.")
else:
    alpha = an.best["alpha"]
    st.caption("Wertgewinn, wenn eine Firma eine andere Menge fährt als abgesprochen und die andere bleibt: im Gleichgewicht (durchgezogen) liegt das Maximum genau bei der "
               "abgesprochenen Menge. Punktiert: derselbe Trigger-Preis-Aufbau mit anderer Auslösewahrscheinlichkeit.")
    curves = _deviation(settings, (alpha, alpha * 0.4, min(0.95, alpha * 2.5)))
    labels = [f"Gleichgewicht, α = {fmt(alpha, 3)}", f"zu träger Trigger, α = {fmt(alpha * 0.4, 3)}", f"zu empfindlicher Trigger, α = {fmt(min(0.95, alpha * 2.5), 3)}"]
    for c, lab in zip(curves, labels):
        c["label"] = lab
    st.plotly_chart(build_deviation(curves), width="stretch", key="deviation_chart")
    st.info("Bei zu trägem Trigger lohnt es sich, mehr zu fahren (der Krieg kommt zu selten). Bei zu empfindlichem Trigger lohnt es sich, **weniger** zu fahren, um nicht "
            "ausgelöst zu werden. Nur eine Einstellung macht die abgesprochene Menge zur besten Antwort.")
st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie viele Gleichgewichte gibt es?")
st.caption("Die Bedingung erster Ordnung für die abgesprochene Menge als Funktion der Auslösewahrscheinlichkeit: wo die Kurve die Null kreuzt (und die globale Prüfung besteht), "
           "ist ein Gleichgewicht.")
st.plotly_chart(build_foc(_foc(settings), list(an.equilibria)), width="stretch", key="foc_chart")
if len(an.equilibria) >= 2:
    lo, hi = sorted(an.equilibria, key=lambda r: r["alpha"])[0], sorted(an.equilibria, key=lambda r: r["alpha"])[-1]
    st.info(f"Es gibt hier **zwei** Gleichgewichte: ein ruhiges mit α = {fmt(lo['alpha'] * 100, 1)} % (Wert {fmt(lo['per_period_value'])} je Periode, "
            f"{fmt(lo['war_share'] * 100, 0)} % der Zeit Krieg) und ein kriegerisches mit α = {fmt(hi['alpha'] * 100, 1)} % (Wert {fmt(hi['per_period_value'])}, "
            f"{fmt(hi['war_share'] * 100, 0)} % Krieg). Beide sind stabil; welches gespielt wird, sagt das Modell nicht.")
elif len(an.equilibria) == 1:
    st.info("Es gibt hier genau ein Gleichgewicht.")
else:
    st.info("Es gibt hier kein Gleichgewicht mit Absprache.")
st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie viel Absprache trägt der Markt?")
st.caption("Bestes Gleichgewicht je Geduld δ (Zeilen) und Schwankung σ (Spalten): höchster Wert je Periode über alle abgesprochenen Mengen (4,5 bis 5,9) und Kriegsdauern "
           "(1 bis 40). Vorgerechnet (tools/precompute.py).")
mat = _table()
st.plotly_chart(build_table(mat), width="stretch", key="table_chart")
st.info("Mit größerer Preisschwankung oder geringerer Geduld bricht die Absprache zusammen: ab σ = 0,30 gibt es bei den gezeigten Werten keine tragbare Absprache mehr, "
        "und selbst im besten Fall liegt der Gewinn nur wenig über Cournot (9,00) und deutlich unter dem Monopol (10,125).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Genau zwei Anbieter, lineare Nachfrage, gleiche Kosten** | Mit mehr Anbietern oder anderer Nachfrage ändern sich Mengen und Schwellen; die Logik des Trigger-Preises bleibt. | - |
| **Nur Preise beobachtbar** | Sähe jeder die Menge des anderen, gäbe es keine Preiskriege im Gleichgewicht (volle Beobachtbarkeit). | `folk-theorem-demo` (perfekte Beobachtung) |
| **Strafe: Rückfall auf Cournot** | Härtere Strafen (Überproduktion) oder andere Strategien können mehr Absprache tragen; hier ist es die einfachste. | - |
| **Schock unabhängig über die Zeit, lognormal** | Korrelierte Nachfrageschocks (Konjunktur) verändern die Kriegshäufigkeit; ein nach oben begrenzter Schock ließe Preiskriege ganz vermeiden. | - |
| **Beide Anbieter folgen dem Trigger-Preis-Plan** | Es ist ein Gleichgewicht, keine Vorhersage: zwei Gleichgewichte mit Absprache und immer Cournot existieren. | - |
| **Ist das Kartellrecht berührt?** | Eine solche Absprache ohne Kommunikation ist hier ein Modell, keine rechtliche Einordnung. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Markt.** Zwei Anbieter, Mengen $q_1, q_2$, $Q = q_1 + q_2$, Preis $p = \theta\,(A - Q)$ mit $\theta = e^{\sigma Z - \sigma^2/2}$ (also $E\theta = 1$), Kosten $c$ je Einheit.
Erwarteter Gewinn $\pi(q, Q) = (A - Q - c)\,q$. Cournot: $Q^c = 2(A-c)/3$, Monopol: $Q^m = (A-c)/2$.

**Strategie.** Absprache bei $Q_c$ (je Anbieter $q_o = Q_c/2$); fällt $p$ unter $\bar p$, $T$ Perioden Cournot, dann zurück. Die Wahrscheinlichkeit des Auslösens bei Absprache ist
$\alpha = P(\theta < \bar p / (A - Q_c))$.

**Werte.** $V = \pi_m + \delta\,[(1-\alpha) V + \alpha W]$ und $W = \pi_c\,\frac{1-\delta^T}{1-\delta} + \delta^T V$, also
$V = \dfrac{\pi_m + \delta\alpha\,\pi_c\,\frac{1-\delta^T}{1-\delta}}{1 - \delta(1-\alpha) - \delta\alpha\,\delta^T}$.

**Anreiz.** Wählt eine Firma $q$ statt $q_o$, ist ihr Wert $V_d(q) = \pi(q, q + q_o) + \delta\,[V + \alpha_q (W - V)]$ mit $\alpha_q = P(\theta < \bar p/(A - q - q_o))$. Gleichgewicht
heißt $V_d(q) \le V$ für alle $q$. Die Bedingung erster Ordnung bei $q_o$: $A - c - 3 q_o = \delta\,(V - W)\,\alpha'(q_o)$ mit $\alpha'(q_o) = f(x)\,x/(A - Q_c)$, $x = F^{-1}(\alpha)$.
Das legt $\alpha$ fest (meist zwei Lösungen).

**Kriegsanteil.** Zwischen zwei Kriegen vergehen im Mittel $1/\alpha$ Absprache-Perioden, danach $T$ Kriegsperioden: der Zeitanteil im Krieg ist $\alpha T/(1 + \alpha T)$.

**Literatur.** Green und Porter (1984), *Noncooperative collusion under imperfect price information*, Econometrica 52, 87–100 (Trigger-Preis-Gleichgewicht, Preiskriege auf dem Gleichgewichtspfad); Abreu, Pearce und Stacchetti (1986), *Optimal cartel equilibria with imperfect monitoring*, Journal of Economic Theory 39, 251–269 (die optimalen symmetrischen Gleichgewichte haben eine andere, einfachere Struktur mit zwei Mengen; hier ist nur die einfache Trigger-Preis-Form gerechnet). Nur Zusammenfassungen gelesen. Die Zahlen zu α, Kriegsanteil und Werten sind hier gerechnet und per Markov-Kette und Monte-Carlo-Simulation geprüft.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
