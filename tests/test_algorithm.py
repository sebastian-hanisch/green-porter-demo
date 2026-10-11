"""Mini-Instanz-Tests je Einheit (DEMO-PLAYBOOK §1b): von Hand gerechnet, A = 10, C = 1, zwei Anbieter."""

import math

import numpy as np
import pytest

import gpo_algorithm as A
import gpo_constants as C


def test_benchmarks_by_hand():
    assert C.Q_MONOPOLY == pytest.approx(4.5) and C.Q_COURNOT == pytest.approx(6.0)
    assert A.stage_profit(2.25, 4.5) == pytest.approx(10.125)       # (10 − 4,5 − 1) · 2,25
    assert A.stage_profit(3.0, 6.0) == pytest.approx(9.0)           # (10 − 6 − 1) · 3
    assert A.stage_profit(0.0, 5.0) == 0.0


def test_lognormal_cdf_pdf_quantile():
    assert float(A.lognormal_cdf(1.0, 0.1)) == pytest.approx(0.5 + 0.5 * math.erf(0.05 / math.sqrt(2)), abs=1e-12)
    assert float(A.lognormal_cdf(1e-12, 0.3)) < 1e-6 and float(A.lognormal_cdf(1e6, 0.3)) > 1 - 1e-9
    for p in (0.01, 0.2, 0.5, 0.9):
        x = A.lognormal_quantile(p, 0.25)
        assert float(A.lognormal_cdf(x, 0.25)) == pytest.approx(p, abs=1e-9)
    assert A.lognormal_pdf(1.0, 0.2) > 0
    with pytest.raises(ValueError):
        A.lognormal_quantile(0.0, 0.2)


def test_the_shock_has_mean_one():
    rng = np.random.default_rng(1)
    z = rng.standard_normal(400000)
    for sigma in (0.1, 0.3, 0.5):
        assert np.mean(np.exp(sigma * z - sigma ** 2 / 2)) == pytest.approx(1.0, abs=0.01)


def test_phase_values_by_hand():
    # Ohne Auslösen (α = 0): V = π_m / (1 − δ). Mit α = 1 und T = 1: V = π_m + δ (π_c + δ V) → V = (π_m + δ π_c) / (1 − δ²).
    v, w = A.phase_values(0.5, 3, 0.0, 10.0, 9.0)
    assert v == pytest.approx(20.0) and w == pytest.approx(9.0 * (1 + 0.5 + 0.25) + 0.125 * 20.0)
    v, w = A.phase_values(0.5, 1, 1.0, 10.0, 9.0)
    assert v == pytest.approx((10.0 + 0.5 * 9.0) / (1 - 0.25)) and w == pytest.approx(9.0 + 0.5 * v)


def test_phase_values_satisfy_their_recursions():
    for delta, t, alpha in ((0.9, 30, 0.05), (0.7, 5, 0.3), (0.95, 1, 0.5)):
        pi_m, pi_c = 10.0, 9.0
        v, w = A.phase_values(delta, t, alpha, pi_m, pi_c)
        assert v == pytest.approx(pi_m + delta * ((1 - alpha) * v + alpha * w))
        assert w == pytest.approx(pi_c * (1 - delta ** t) / (1 - delta) + delta ** t * v)


def test_phase_values_validate():
    with pytest.raises(ValueError):
        A.phase_values(1.0, 5, 0.1, 10.0, 9.0)
    with pytest.raises(ValueError):
        A.phase_values(0.9, 0, 0.1, 10.0, 9.0)


def test_trigger_price_is_the_alpha_quantile_of_the_price():
    for alpha in (0.02, 0.1, 0.5):
        p_bar = A.trigger_price(0.2, 5.0, alpha)
        assert float(A.lognormal_cdf(p_bar / (10.0 - 5.0), 0.2)) == pytest.approx(alpha, abs=1e-9)


def test_deviation_curve_at_the_agreed_quantity_equals_v():
    d = A.deviation_curve(0.9, 0.1, 5.3, 30, 0.1)
    i = int(np.where(np.isclose(d["q"], 5.3 / 2))[0][0])
    assert d["value"][i] == pytest.approx(d["V"], abs=1e-9)
    assert d["alpha_q"][i] == pytest.approx(0.1, abs=1e-9)
    assert np.all(np.diff(d["alpha_q"]) >= -1e-12)                    # mehr Menge -> niedrigerer Preis -> häufiger ausgelöst


def test_foc_matches_the_numerical_derivative():
    delta, sigma, qc, t = 0.9, 0.1, 5.3, 30
    for alpha in (0.03, 0.1, 0.4):
        pi_m = A.stage_profit(qc / 2, qc)
        pi_c = A.stage_profit(3.0, 6.0)
        v, w = A.phase_values(delta, t, alpha, pi_m, pi_c)
        p_bar = A.trigger_price(sigma, qc, alpha)

        def vd(q):
            total = q + qc / 2
            a_q = float(A.lognormal_cdf(p_bar / (10.0 - total), sigma))
            return (10.0 - total - 1.0) * q + delta * ((1 - a_q) * v + a_q * w)

        h = 1e-5
        numeric = (vd(qc / 2 + h) - vd(qc / 2 - h)) / (2 * h)
        assert A.foc_gap(delta, sigma, qc, t, alpha) == pytest.approx(numeric, abs=1e-5), alpha


def test_equilibria_have_a_vanishing_gap_and_two_solutions_at_the_default():
    eq = A.equilibria(0.9, 0.1, 5.3, 30)
    assert len(eq) == 2
    assert eq[0]["alpha"] == pytest.approx(0.0487, abs=0.0005) and eq[1]["alpha"] == pytest.approx(0.5326, abs=0.001)
    for e in eq:
        assert abs(e["gap"]) < 1e-4
        assert A.foc_gap(0.9, 0.1, 5.3, 30, e["alpha"]) == pytest.approx(0.0, abs=1e-6)
    assert eq[0]["V"] > eq[1]["V"]


def test_no_equilibrium_cases():
    assert A.equilibria(0.9, 0.1, 5.3, 3) == []          # Strafe zu kurz
    assert A.equilibria(0.7, 0.1, 5.3, 30) == []         # zu ungeduldig
    assert A.equilibria(0.9, 0.5, 5.3, 30) == []         # zu verrauscht
    assert A.best_equilibrium(0.9, 0.5, 5.3, 30) is None


def test_war_share_formula():
    e = A.best_equilibrium(0.9, 0.1, 5.3, 30)
    assert e["war_share"] == pytest.approx(e["alpha"] * 30 / (1 + e["alpha"] * 30))
    assert e["long_run_profit"] == pytest.approx((e["profit_collusion"] + e["alpha"] * 30 * 9.0) / (1 + e["alpha"] * 30))


def test_simulate_shapes_and_phases():
    s = A.simulate(0.9, 0.1, 5.3, 5, 0.1, 500, 1)
    assert len(s["price"]) == 500 and set(np.unique(s["phase"])) <= {0, 1}
    # Nach jedem Auslöser folgen genau T Kriegsperioden
    idx = np.where(s["trigger"])[0]
    for i in idx[:5]:
        if i + 5 < 500:
            assert s["phase"][i + 1: i + 6].tolist() == [1] * 5
    assert np.all(s["quantity"][s["phase"] == 1] == 6.0) and np.all(s["quantity"][s["phase"] == 0] == 5.3)
    again = A.simulate(0.9, 0.1, 5.3, 5, 0.1, 500, 1)
    assert np.array_equal(again["price"], s["price"])
