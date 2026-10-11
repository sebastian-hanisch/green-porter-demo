"""Kern der Demo (numpy): Preiskriege im Gleichgewicht bei verrauschter Nachfrage (Green und Porter 1984).

Zwei Anbieter wählen Mengen, sehen nur den Marktpreis p = θ · (A − Q) mit lognormalem Schock θ (Erwartung 1), nicht die Menge des anderen. Strategie
(Trigger-Preis): in der Absprache-Phase je Anbieter die Menge Qc/2; fällt der Preis unter den Trigger p̄, spielen beide T Perioden lang die Cournot-Menge
(„Preiskrieg“), danach wieder die Absprache. Der Trigger p̄ ist nicht frei wählbar: die abgesprochene Menge muss die beste Antwort sein, das legt die
Wahrscheinlichkeit α fest, mit der der Trigger auch ohne Abweichen auslöst. Einheiten (DEMO-PLAYBOOK §1b):

- `lognormal_cdf`, `lognormal_pdf`, `lognormal_quantile`   Verteilung des Schocks
- `stage_profit`          erwarteter Gewinn einer Firma bei Menge q und Gesamtmenge Q
- `phase_values`          Wert der Absprache-Phase V und der Kriegsphase W (lineares System, exakt)
- `deviation_curve`       Wert V_d(q) jeder einseitigen Mengenwahl q aus der Absprache-Phase
- `incentive_gap`         max_q V_d(q) − V (kleiner oder gleich null heißt: keine Abweichung lohnt)
- `foc_gap`               Bedingung erster Ordnung für die abgesprochene Menge in α
- `equilibria`            alle α, für die die Absprache ein Gleichgewicht ist (Nullstellen der FOC, global geprüft)
- `simulate`              eine Preisreihe mit Phasen"""

import math
from statistics import NormalDist

import numpy as np

import gpo_constants as C

_N = NormalDist()


def lognormal_cdf(x, sigma: float):
    """P(θ ≤ x) für θ = exp(σ Z − σ²/2) (Erwartung 1); `x` skalar oder Feld."""
    arr = np.maximum(np.asarray(x, dtype=float), 1e-300)
    z = (np.log(arr) + sigma ** 2 / 2.0) / sigma
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))


def lognormal_pdf(x: float, sigma: float) -> float:
    """Dichte von θ an der Stelle x."""
    z = (math.log(x) + sigma ** 2 / 2.0) / sigma
    return math.exp(-0.5 * z * z) / (math.sqrt(2.0 * math.pi) * sigma * x)


def lognormal_quantile(p: float, sigma: float) -> float:
    """Der Wert x mit P(θ ≤ x) = p."""
    if not 0.0 < p < 1.0:
        raise ValueError("p muss in (0, 1) liegen")
    return math.exp(sigma * _N.inv_cdf(p) - sigma ** 2 / 2.0)


def stage_profit(q: float, total: float) -> float:
    """Erwarteter Gewinn einer Firma mit Menge q bei Gesamtmenge `total`: (A − Q − C) · q (E[θ] = 1)."""
    return (C.A - total - C.C) * q


def phase_values(delta: float, t: int, alpha: float, profit_collusion: float, profit_cournot: float) -> tuple[float, float]:
    """(V, W): Wert der Absprache-Phase und Wert zu Beginn einer Kriegsphase der Länge `t`.

    V = π_m + δ [ (1 − α) V + α W ],  W = π_c (1 − δ^t)/(1 − δ) + δ^t V."""
    if not 0.0 < delta < 1.0:
        raise ValueError("δ muss in (0, 1) liegen")
    if t < 1:
        raise ValueError("Kriegsdauer mindestens 1")
    geo = (1.0 - delta ** t) / (1.0 - delta)
    denom = 1.0 - delta * (1.0 - alpha) - delta * alpha * delta ** t
    v = (profit_collusion + delta * alpha * profit_cournot * geo) / denom
    w = profit_cournot * geo + delta ** t * v
    return float(v), float(w)


def trigger_price(sigma: float, qc: float, alpha: float) -> float:
    """Trigger-Preis p̄: der α-Quantil-Preis bei der abgesprochenen Gesamtmenge, p̄ = (A − Qc) · F⁻¹(α)."""
    return (C.A - qc) * lognormal_quantile(alpha, sigma)


def _profits(qc: float) -> tuple[float, float]:
    return stage_profit(qc / 2.0, qc), stage_profit(C.Q_COURNOT / 2.0, C.Q_COURNOT)


def deviation_curve(delta: float, sigma: float, qc: float, t: int, alpha: float, n: int = C.DEVIATION_GRID_N) -> dict:
    """Wert V_d(q) jeder Menge q einer Firma aus der Absprache-Phase, während die andere bei Qc/2 bleibt:

    V_d(q) = π(q, q + Qc/2) + δ [ (1 − α_q) V + α_q W ],  α_q = P(θ (A − q − Qc/2) < p̄). Bei q = Qc/2 ist V_d = V."""
    pi_m, pi_c = _profits(qc)
    v, w = phase_values(delta, t, alpha, pi_m, pi_c)
    p_bar = trigger_price(sigma, qc, alpha)
    q_other = qc / 2.0
    q = np.unique(np.append(np.linspace(0.0, C.A - C.C, n), q_other))
    total = q + q_other
    price = np.maximum(C.A - total, 1e-9)
    alpha_q = lognormal_cdf(p_bar / price, sigma)
    value = (C.A - total - C.C) * q + delta * ((1.0 - alpha_q) * v + alpha_q * w)
    return {"q": q, "value": value, "alpha_q": alpha_q, "V": v, "W": w, "p_bar": p_bar, "q_other": q_other}


def incentive_gap(delta: float, sigma: float, qc: float, t: int, alpha: float) -> float:
    """max_q V_d(q) − V. Genau dann ≤ 0 (bis auf Rechengenauigkeit), wenn keine einseitige Mengenwahl besser ist als die abgesprochene."""
    d = deviation_curve(delta, sigma, qc, t, alpha)
    return float(np.max(d["value"]) - d["V"])


def foc_gap(delta: float, sigma: float, qc: float, t: int, alpha: float) -> float:
    """Ableitung von V_d nach q an der abgesprochenen Menge: π'(q_o) − δ (V − W) · α'(q_o). Nullstelle in α = Bedingung erster Ordnung.

    π'(q_o) = A − C − 3 q_o; α'(q_o) = f(x) · p̄ / (A − Qc)² mit x = F⁻¹(α) und f x = φ(z)/σ, z = Φ⁻¹(α)."""
    pi_m, pi_c = _profits(qc)
    v, w = phase_values(delta, t, alpha, pi_m, pi_c)
    x = lognormal_quantile(alpha, sigma)
    f_x = lognormal_pdf(x, sigma)
    dalpha = f_x * x / (C.A - qc)                 # dα_q/dq an der Stelle q_o (p̄/(A−Qc)² = x/(A−Qc))
    return (C.A - C.C - 3.0 * qc / 2.0) - delta * (v - w) * dalpha


def equilibria(delta: float, sigma: float, qc: float, t: int, tol: float = 1e-4) -> list[dict]:
    """Alle α, bei denen die Absprache bei Qc, Strafdauer t ein Gleichgewicht ist: Nullstellen der FOC (feine Suche plus Bisektion), global geprüft
    (kein q hat einen höheren Wert als V, bis auf `tol`). Sortiert nach V absteigend."""
    grid = np.linspace(0.0005, 0.9995, 800)
    values = [foc_gap(delta, sigma, qc, t, float(a)) for a in grid]
    roots = []
    for a0, a1, g0, g1 in zip(grid[:-1], grid[1:], values[:-1], values[1:]):
        if g0 == 0.0:
            roots.append(float(a0))
        elif g0 * g1 < 0.0:
            lo, hi, glo = float(a0), float(a1), g0
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                gm = foc_gap(delta, sigma, qc, t, mid)
                if glo * gm <= 0.0:
                    hi = mid
                else:
                    lo, glo = mid, gm
            roots.append(0.5 * (lo + hi))
    out = []
    for a in roots:
        if incentive_gap(delta, sigma, qc, t, a) <= tol:
            pi_m, pi_c = _profits(qc)
            v, w = phase_values(delta, t, a, pi_m, pi_c)
            out.append({
                "alpha": a, "V": v, "W": w, "trigger_price": trigger_price(sigma, qc, a), "profit_collusion": pi_m, "profit_cournot": pi_c,
                "per_period_value": (1.0 - delta) * v, "war_share": a * t / (1.0 + a * t),
                "long_run_profit": (pi_m + a * t * pi_c) / (1.0 + a * t), "gap": incentive_gap(delta, sigma, qc, t, a),
            })
    return sorted(out, key=lambda r: -r["V"])


def best_equilibrium(delta: float, sigma: float, qc: float, t: int) -> dict | None:
    """Das Gleichgewicht mit dem höchsten Wert (oder None, wenn es bei diesem Qc und T keines gibt)."""
    eq = equilibria(delta, sigma, qc, t)
    return eq[0] if eq else None


def simulate(delta: float, sigma: float, qc: float, t: int, alpha: float, steps: int, seed: int) -> dict:
    """Eine Preisreihe: Phase je Periode (0 = Absprache, 1 = Krieg), Gesamtmenge, Preis, Auslöser. Beide halten sich an die Strategie, keiner weicht ab."""
    rng = np.random.default_rng(seed)
    p_bar = trigger_price(sigma, qc, alpha)
    phase, quantity, price, trigger = [], [], [], []
    war_left = 0
    for _ in range(steps):
        in_war = war_left > 0
        total = C.Q_COURNOT if in_war else qc
        theta = math.exp(sigma * rng.standard_normal() - sigma ** 2 / 2.0)
        p = theta * (C.A - total)
        phase.append(1 if in_war else 0)
        quantity.append(total)
        price.append(p)
        if in_war:
            war_left -= 1
            trigger.append(False)
        else:
            fire = p < p_bar
            trigger.append(bool(fire))
            if fire:
                war_left = t
    return {"phase": np.array(phase), "quantity": np.array(quantity), "price": np.array(price), "trigger": np.array(trigger), "p_bar": p_bar}
