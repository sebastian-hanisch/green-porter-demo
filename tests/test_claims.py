"""Jede Zahl aus README und App wird hier über die echten Auswertungsfunktionen nachgerechnet (DEMO-PLAYBOOK §4)."""

import json
import pathlib

import pytest

import gpo_algorithm as A
import gpo_constants as C
import gpo_evaluation as E


def test_benchmarks():
    assert E.PI_MONOPOLY == pytest.approx(10.125) and E.PI_COURNOT == pytest.approx(9.0)


def test_default_equilibria():
    eq = A.equilibria(0.9, 0.1, 5.3, 30)
    assert [round(e["alpha"], 3) for e in eq] == [0.049, 0.533]
    assert [round(e["per_period_value"], 3) for e in eq] == [9.567, 9.144]
    assert [round(e["war_share"], 2) for e in eq] == [0.59, 0.94]
    assert eq[0]["long_run_profit"] == pytest.approx(9.327, abs=0.001)
    assert eq[0]["trigger_price"] == pytest.approx(3.962, abs=0.002)


def test_default_analysis():
    an = E.analyse(E.Settings())
    assert an.best["alpha"] == pytest.approx(0.0487, abs=0.0005)
    assert an.share_of_rent == pytest.approx(0.504, abs=0.002)                  # etwa die Hälfte der Absprache-Rente
    assert an.sim_triggers >= 1 and an.sim_steps == 400
    assert E.verdict(an, E.Settings())[0] == "info" and "ohne dass jemand abgewichen ist" in E.verdict(an, E.Settings())[1]


def test_tighter_collusion_needs_more_wars():
    eq = A.equilibria(0.9, 0.1, 4.8, 30)
    assert [round(e["alpha"], 3) for e in eq] == [0.137, 0.253]
    assert [round(e["per_period_value"], 3) for e in eq] == [9.495, 9.34]
    assert eq[0]["war_share"] == pytest.approx(0.80, abs=0.005)


def test_very_patient_firms_sustain_a_tighter_collusion_with_fewer_triggers():
    eq = A.equilibria(0.97, 0.1, 5.0, 30)
    assert [round(e["alpha"], 3) for e in eq] == [0.024, 0.480]
    assert eq[0]["per_period_value"] == pytest.approx(9.681, abs=0.001) and eq[0]["war_share"] == pytest.approx(0.42, abs=0.01)


def test_no_equilibrium_presets():
    for name in ("Kurze Strafphase (T = 3)", "Sehr verrauschter Markt (σ = 0,50)"):
        p = C.PRESETS[name]
        an = E.analyse(E.Settings(p["delta"], p["sigma"], p["qc"], p["t"]))
        assert an.best is None and an.sim is None
        level, text = E.verdict(an, E.Settings(p["delta"], p["sigma"], p["qc"], p["t"]))
        assert level == "warning" and "keine tragbare Absprache" in text


def test_table_cells_by_recomputation():
    data = json.loads((pathlib.Path(__file__).resolve().parent.parent / "gpo_data.json").read_text(encoding="utf-8"))
    cells = data["cells"]
    assert cells["0.9|0.1"]["per_period_value"] == pytest.approx(9.609, abs=0.001) and cells["0.9|0.1"]["t"] == 40 and cells["0.9|0.1"]["qc"] == pytest.approx(5.1)
    assert cells["0.5|0.1"] is None and cells["0.9|0.3"] is None and cells["0.7|0.15"] is None
    assert cells["0.95|0.05"]["per_period_value"] == pytest.approx(9.903, abs=0.001)
    # Stichprobe neu gerechnet
    for key in ("0.9|0.1", "0.95|0.2", "0.7|0.1"):
        d, s = (float(x) for x in key.split("|"))
        best = None
        for qc in C.QC_GRID:
            if qc >= C.Q_COURNOT - 1e-9:
                continue
            for t in C.T_GRID:
                e = A.best_equilibrium(d, s, float(qc), t)
                if e and (best is None or e["per_period_value"] > best["per_period_value"] + 1e-12):
                    best = e
        assert best["per_period_value"] == pytest.approx(cells[key]["per_period_value"], abs=1e-9), key


def test_collusion_disappears_with_noise_and_impatience_in_the_table():
    m = E.table_matrix()
    z = {(d, s): v for d, row in zip(m["deltas"], m["z"]) for s, v in zip(m["sigmas"], row)}
    assert z[(0.5, 0.05)] is not None and z[(0.5, 0.1)] is None
    assert z[(0.95, 0.2)] is not None and z[(0.95, 0.3)] is None
    values = [v for v in z.values() if v is not None]
    assert min(values) > 9.0 and max(values) < E.PI_MONOPOLY               # immer zwischen Cournot und Monopol


def test_simulated_war_share_converges_to_the_formula():
    s = A.simulate(0.9, 0.1, 5.3, 30, 0.0487, 300000, 3)
    assert s["phase"].mean() == pytest.approx(0.0487 * 30 / (1 + 0.0487 * 30), abs=0.02)
    assert s["trigger"][s["phase"] == 0].mean() == pytest.approx(0.0487, abs=0.004)


def test_a_too_sluggish_trigger_invites_overproduction_and_a_too_sensitive_one_invites_underproduction():
    import numpy as np
    alpha = A.equilibria(0.9, 0.1, 5.3, 30)[0]["alpha"]
    q_o = 5.3 / 2
    for factor, expect_more in ((0.4, True), (2.5, False)):
        d = A.deviation_curve(0.9, 0.1, 5.3, 30, alpha * factor)
        best_q = float(d["q"][int(np.argmax(d["value"]))])
        assert (best_q > q_o) == expect_more, (factor, best_q)
        assert np.max(d["value"]) - d["V"] > 1e-3
