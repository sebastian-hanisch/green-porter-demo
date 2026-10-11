"""Orakel-Tests green-porter-demo: der Kern wird gegen UNABHÄNGIGE Rechenwege geprüft (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK §2).

1. Werte und Kriegsanteil: die Markov-Kette über (Absprache, Krieg mit k verbleibenden Perioden) als explizite Übergangsmatrix; V per linearem System,
   Zeitanteil per Dauerverteilung (statt der geschlossenen Formeln des Kerns).
2. Wert einer Abweichung: Monte-Carlo-Simulation vieler Pfade mit Preisschock, Trigger und Krieg, erste Periode mit der abweichenden Menge, danach Einhalten;
   gegen V_d(q) des Kerns.
3. Gleichgewicht: die globale Bedingung V ≥ V_d(q) auf einem sehr dichten Mengenraster, und dass Einstellungen neben den Nullstellen verletzt sind.
4. Die FOC-Nullstellen sind genau die α, für die die Ableitung von V_d an der abgesprochenen Menge verschwindet (zentrale Differenz)."""

import math

import numpy as np
import pytest

import gpo_algorithm as A
import gpo_constants as C


def chain(t: int, alpha: float):
    """Zustände 0 = Absprache, k = 1..t Krieg mit k noch ausstehenden Perioden (Kriegsperiode k = t ist die erste). Übergangsmatrix."""
    n = t + 1
    p = np.zeros((n, n))
    p[0, 0] = 1.0 - alpha
    p[0, t] = alpha                       # nach dem Auslösen beginnt der Krieg mit t ausstehenden Perioden
    for k in range(t, 1, -1):
        p[k, k - 1] = 1.0
    p[1, 0] = 1.0
    return p


def values_from_chain(delta, t, alpha, pi_m, pi_c):
    p = chain(t, alpha)
    reward = np.array([pi_m] + [pi_c] * t)
    v = np.linalg.solve(np.eye(t + 1) - delta * p, reward)
    return float(v[0]), float(v[t])      # V im Zustand Absprache, W im ersten Kriegszustand


@pytest.mark.parametrize("delta,t,alpha", [(0.9, 30, 0.05), (0.9, 5, 0.3), (0.7, 1, 0.5), (0.97, 12, 0.02)])
def test_values_match_the_explicit_markov_chain(delta, t, alpha):
    v, w = A.phase_values(delta, t, alpha, 10.0, 9.0)
    v2, w2 = values_from_chain(delta, t, alpha, 10.0, 9.0)
    assert v == pytest.approx(v2, abs=1e-9) and w == pytest.approx(w2, abs=1e-9)


@pytest.mark.parametrize("t,alpha", [(30, 0.05), (5, 0.3), (1, 0.5), (12, 0.02)])
def test_war_share_matches_the_stationary_distribution(t, alpha):
    p = chain(t, alpha)
    dist = np.full(t + 1, 1.0 / (t + 1))
    for _ in range(20000):
        dist = dist @ p
    assert 1.0 - dist[0] == pytest.approx(alpha * t / (1 + alpha * t), abs=1e-6)


def mc_deviation_value(delta, sigma, qc, t, alpha, q, runs=60000, horizon=500, seed=11):
    """Erwarteter diskontierter Gewinn einer Firma, die in Periode 1 die Menge q fährt und danach die abgesprochene (die andere hält immer ein)."""
    rng = np.random.default_rng(seed)
    q_o = qc / 2.0
    p_bar = A.trigger_price(sigma, qc, alpha)
    pi_c = A.stage_profit(3.0, 6.0)
    total = np.zeros(runs)
    war_left = np.zeros(runs, dtype=int)
    for period in range(horizon):
        in_war = war_left > 0
        theta = np.exp(sigma * rng.standard_normal(runs) - sigma ** 2 / 2.0)
        if period == 0:
            quantity_total = np.full(runs, q + q_o)
            own = np.full(runs, q)
            profit = (theta * (C.A - quantity_total) - C.C) * own
        else:
            quantity_total = np.where(in_war, C.Q_COURNOT, qc)
            own = np.where(in_war, 3.0, q_o)
            profit = (theta * (C.A - quantity_total) - C.C) * own
        price = theta * (C.A - quantity_total)
        total += delta ** period * profit
        new_war = np.where(in_war, war_left - 1, np.where(price < p_bar, t, 0))
        war_left = new_war
    return float(total.mean()), float(total.std() / math.sqrt(runs))


@pytest.mark.parametrize("q", [2.65, 2.9, 3.2, 2.3])
def test_deviation_value_matches_a_monte_carlo_simulation(q):
    delta, sigma, qc, t, alpha = 0.9, 0.1, 5.3, 10, 0.1
    d = A.deviation_curve(delta, sigma, qc, t, alpha)
    i = int(np.argmin(np.abs(d["q"] - q)))
    mean, se = mc_deviation_value(delta, sigma, qc, t, alpha, float(d["q"][i]))
    assert abs(mean - d["value"][i]) < 4 * se + 0.05, (q, mean, d["value"][i], se)


def test_equilibria_satisfy_the_global_condition_on_a_dense_grid():
    for delta, sigma, qc, t in ((0.9, 0.1, 5.3, 30), (0.9, 0.1, 4.8, 30), (0.97, 0.1, 5.0, 30), (0.9, 0.15, 5.6, 40)):
        for e in A.equilibria(delta, sigma, qc, t):
            d = A.deviation_curve(delta, sigma, qc, t, e["alpha"], n=4000)
            assert np.max(d["value"]) - d["V"] < 1e-4, (delta, sigma, qc, t, e["alpha"])


def test_settings_away_from_the_roots_are_not_equilibria():
    delta, sigma, qc, t = 0.9, 0.1, 5.3, 30
    roots = [e["alpha"] for e in A.equilibria(delta, sigma, qc, t)]
    for a in (0.01, 0.1, 0.3, 0.7):
        assert min(abs(a - r) for r in roots) > 0.005
        assert A.incentive_gap(delta, sigma, qc, t, a) > 1e-3, a


def test_roots_are_the_zeros_of_the_central_difference_of_v_d():
    delta, sigma, qc, t = 0.9, 0.1, 5.3, 30
    for e in A.equilibria(delta, sigma, qc, t):
        a = e["alpha"]
        pi_m, pi_c = A.stage_profit(qc / 2, qc), A.stage_profit(3.0, 6.0)
        v, w = A.phase_values(delta, t, a, pi_m, pi_c)
        p_bar = A.trigger_price(sigma, qc, a)

        def vd(q):
            total = q + qc / 2
            a_q = float(A.lognormal_cdf(p_bar / (C.A - total), sigma))
            return (C.A - total - C.C) * q + delta * ((1 - a_q) * v + a_q * w)

        h = 1e-4
        assert (vd(qc / 2 + h) - vd(qc / 2 - h)) / (2 * h) == pytest.approx(0.0, abs=1e-4)


def test_equilibrium_existence_is_monotone_in_patience_on_a_sample():
    sigma, qc, t = 0.1, 5.3, 30
    exists = [bool(A.equilibria(d, sigma, qc, t)) for d in (0.6, 0.7, 0.8, 0.9, 0.95)]
    assert exists == sorted(exists)                      # ab einer Geduld an existiert es und bleibt bestehen
