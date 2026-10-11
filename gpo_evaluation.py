"""Kennzahlen, Verdikt-Logik und Auswertungen über den Kern (die Komposition der Einheiten aus gpo_algorithm)."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import gpo_algorithm as A
import gpo_constants as C

DATA_FILE = Path(__file__).resolve().parent / "gpo_data.json"
PI_MONOPOLY = A.stage_profit(C.Q_MONOPOLY / 2.0, C.Q_MONOPOLY)        # 10,125 je Firma
PI_COURNOT = A.stage_profit(C.Q_COURNOT / 2.0, C.Q_COURNOT)           # 9,0 je Firma


def fmt(x: float, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


@dataclass(frozen=True)
class Settings:
    delta: float = C.DEFAULT_DELTA
    sigma: float = C.DEFAULT_SIGMA
    qc: float = C.DEFAULT_QC
    t: int = C.DEFAULT_T
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Analysis:
    equilibria: tuple[dict, ...]
    best: dict | None
    share_of_rent: float | None                   # Anteil des Abstands Cournot → Monopol, den das beste Gleichgewicht erreicht
    sim_war_share: float | None
    sim_triggers: int | None
    sim_steps: int
    sim: dict | None


def analyse(settings: Settings, steps: int = C.SIM_STEPS) -> Analysis:
    eq = A.equilibria(settings.delta, settings.sigma, settings.qc, settings.t)
    best = eq[0] if eq else None
    sim = share = sim_war = triggers = None
    if best is not None:
        sim = A.simulate(settings.delta, settings.sigma, settings.qc, settings.t, best["alpha"], steps, settings.seed)
        sim_war = float(sim["phase"].mean())
        triggers = int(sim["trigger"].sum())
        share = (best["per_period_value"] - PI_COURNOT) / (PI_MONOPOLY - PI_COURNOT)
    return Analysis(tuple(eq), best, share, sim_war, triggers, steps, sim)


def foc_curve(settings: Settings, n: int = 400) -> dict:
    alphas = np.linspace(0.002, 0.998, n)
    return {"alpha": alphas.tolist(), "foc": [A.foc_gap(settings.delta, settings.sigma, settings.qc, settings.t, float(a)) for a in alphas]}


def deviation_curves(settings: Settings, alphas: list[float]) -> list[dict]:
    """V_d(q) − V für mehrere Auslösewahrscheinlichkeiten (Gleichgewicht und vom Gleichgewicht abweichende Einstellungen)."""
    out = []
    for a in alphas:
        d = A.deviation_curve(settings.delta, settings.sigma, settings.qc, settings.t, a)
        out.append({"alpha": a, "q": d["q"].tolist(), "gain": (d["value"] - d["V"]).tolist(), "q_other": d["q_other"]})
    return out


def load_table() -> dict:
    """Vorgerechnete Tabelle: bestes Gleichgewicht je (δ, σ) über Qc und T (tools/precompute.py)."""
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def table_matrix() -> dict:
    data = load_table()
    deltas, sigmas = data["deltas"], data["sigmas"]
    z = []
    for d in deltas:
        z.append([None if data["cells"][f"{d}|{s}"] is None else data["cells"][f"{d}|{s}"]["per_period_value"] for s in sigmas])
    return {"deltas": deltas, "sigmas": sigmas, "z": z, "cells": data["cells"]}


def verdict(an: Analysis, settings: Settings) -> tuple[str, str]:
    """(Stufe, Satz) für die Kernfrage: gibt es Preiskriege, obwohl keiner abweicht?"""
    if an.best is None:
        return "warning", (f"Bei Menge {fmt(settings.qc)} und Strafdauer {settings.t} gibt es **keine tragbare Absprache**: kein Auslöse-Niveau macht die abgesprochene Menge zur "
                           "besten Antwort. Übrig bleibt Cournot (Gewinn 9,00 je Firma).")
    b = an.best
    return "info", (f"Die Absprache ist ein Gleichgewicht. Der Trigger-Preis liegt bei {fmt(b['trigger_price'])}; er löst auch ohne jedes Abweichen mit Wahrscheinlichkeit "
                    f"**{fmt(b['alpha'] * 100, 1)} %** je Absprache-Periode aus. In der Simulation gab es {an.sim_triggers} Preiskriege in {an.sim_steps} Perioden, "
                    f"**ohne dass jemand abgewichen ist**; im Mittel verbringen die Anbieter {fmt(b['war_share'] * 100, 0)} % der Zeit im Krieg.")
