"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzen."""

import gpo_constants as C
import gpo_evaluation as ev
import gpo_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, preset in C.PRESETS.items():
        assert C.DELTA_MIN <= preset["delta"] <= C.DELTA_MAX, name
        assert C.SIGMA_MIN <= preset["sigma"] <= C.SIGMA_MAX, name
        assert C.QC_MIN <= preset["qc"] <= C.QC_MAX and C.T_MIN <= preset["t"] <= C.T_MAX, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(first["delta"], first["sigma"], first["qc"], first["t"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) <= set(P.SETTING_SPECS)


def test_clamp_limits_numbers():
    spec = P.SETTING_SPECS["t_slider"]
    assert P.clamp(spec, 999) == C.T_MAX and P.clamp(spec, 0) == C.T_MIN


def test_preset_stories_hold():
    def run(name):
        p = C.PRESETS[name]
        return ev.analyse(ev.Settings(p["delta"], p["sigma"], p["qc"], p["t"]))

    assert run("Voreinstellung (δ = 0,90, σ = 0,10)").best is not None
    assert run("Kurze Strafphase (T = 3)").best is None
    tight = run("Engere Absprache (Menge 4,8)")
    assert tight.best is not None and tight.best["war_share"] > 0.75           # „rund 80 % der Zeit“
    assert run("Sehr geduldig (δ = 0,97)").best is not None
    assert run("Sehr verrauschter Markt (σ = 0,50)").best is None
