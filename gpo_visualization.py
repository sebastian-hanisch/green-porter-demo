"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go

import gpo_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", y=-0.25))
    return lock_axes(fig)


def build_price_series(sim):
    """Preisreihe der Simulation: Punkte je Periode (grün = Absprache-Phase, rot = Krieg), der Trigger-Preis als Linie, Auslöser markiert."""
    n = len(sim["price"])
    x = np.arange(1, n + 1)
    phase = sim["phase"]
    fig = go.Figure()
    for flag, name, color in ((0, "Absprache-Phase", C.COLOR_COLLUSION), (1, "Preiskrieg", C.COLOR_WAR)):
        sel = phase == flag
        fig.add_trace(go.Scatter(x=x[sel], y=sim["price"][sel], mode="markers", name=name, marker=dict(size=6, color=color),
                                 hovertemplate="Periode %{x}: Preis %{y:.2f}<extra>" + name + "</extra>"))
    trig = sim["trigger"]
    fig.add_trace(go.Scatter(x=x[trig], y=sim["price"][trig], mode="markers", name="löst den Krieg aus",
                             marker=dict(size=12, color=C.COLOR_WAR, symbol="x"), hovertemplate="Periode %{x}: Auslöser, Preis %{y:.2f}<extra></extra>"))
    fig.add_hline(y=sim["p_bar"], line=dict(color="rgba(60,60,60,0.8)", width=1.5, dash="dash"), annotation_text="Trigger-Preis", annotation_position="top left")
    fig.update_xaxes(title_text="Periode")
    fig.update_yaxes(title_text="Marktpreis")
    return _base(fig, height=400)


def build_deviation(curves):
    """Wertgewinn V_d(q) − V durch eine einseitig andere Menge q; die abgesprochene Menge ist markiert. Beim Gleichgewicht liegt das Maximum bei null."""
    fig = go.Figure()
    for k, c in enumerate(curves):
        fig.add_trace(go.Scatter(x=c["q"], y=c["gain"], mode="lines", name=c["label"], line=dict(width=4 if k == 0 else 2, dash=None if k == 0 else "dot"),
                                 hovertemplate="Menge %{x:.2f}: %{y:.3f}<extra></extra>"))
    q_other = curves[0]["q_other"]
    fig.add_vline(x=q_other, line=dict(color="rgba(60,60,60,0.7)", width=1.5, dash="dash"), annotation_text="abgesprochene Menge", annotation_position="top left")
    fig.add_hline(y=0.0, line=dict(color="rgba(60,60,60,0.5)", width=1))
    fig.update_xaxes(title_text="Menge einer Firma (die andere bleibt bei der abgesprochenen)", range=[1.5, 4.0])
    fig.update_yaxes(title_text="Wertgewinn gegenüber Einhalten (V_d − V)")
    return _base(fig, height=380)


def build_foc(curve, roots):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve["alpha"], y=curve["foc"], mode="lines", name="Grenzgewinn des Mehrproduzierens", line=dict(color=C.COLOR_LINE, width=4),
                             hovertemplate="α = %{x:.3f}: %{y:.3f}<extra></extra>"))
    fig.add_hline(y=0.0, line=dict(color="rgba(60,60,60,0.7)", width=1.5))
    if roots:
        fig.add_trace(go.Scatter(x=[r["alpha"] for r in roots], y=[0.0] * len(roots), mode="markers", name="Gleichgewicht",
                                 marker=dict(size=14, color=C.COLOR_WAR, symbol="diamond"), hovertemplate="α = %{x:.3f}<extra>Gleichgewicht</extra>"))
    fig.update_xaxes(title_text="Auslösewahrscheinlichkeit α des Triggers bei Absprache", range=[0, 1])
    fig.update_yaxes(title_text="Ableitung des Werts nach der Menge an der abgesprochenen Stelle")
    return _base(fig, height=360)


def build_table(matrix):
    z = [[np.nan if v is None else v for v in row] for row in matrix["z"]]
    text = [["keine" if v is None else f"{v:.2f}".replace(".", ",") for v in row] for row in matrix["z"]]
    fig = go.Figure(go.Heatmap(z=z, x=[f"{s:.2f}".replace(".", ",") for s in matrix["sigmas"]], y=[f"{d:.2f}".replace(".", ",") for d in matrix["deltas"]],
                               text=text, texttemplate="%{text}", zmin=9.0, zmax=10.125, colorscale="Teal", xgap=2, ygap=2,
                               colorbar=dict(title="Gewinn je<br>Periode"), hovertemplate="δ = %{y}, σ = %{x}: %{text}<extra></extra>"))
    fig.update_xaxes(title_text="Schwankung des Preises σ", type="category")
    fig.update_yaxes(title_text="Geduld δ", type="category", autorange="reversed")
    return _base(fig, height=380, legend=False)
