"""Rechnet die Tabelle „bestes Gleichgewicht je δ und σ“ vor und schreibt gpo_data.json.

Aufruf (aus dem Demo-Ordner): python tools/precompute.py
Je (δ, σ): über alle Qc aus QC_GRID und alle T aus T_GRID das Gleichgewicht mit dem höchsten Wert je Periode. Deterministisch; tests/test_claims.py rechnet Zellen nach."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import gpo_algorithm as A  # noqa: E402
import gpo_constants as C  # noqa: E402


def best_cell(delta: float, sigma: float) -> dict | None:
    best = None
    for qc in C.QC_GRID:
        if qc >= C.Q_COURNOT - 1e-9:
            continue
        for t in C.T_GRID:
            e = A.best_equilibrium(delta, sigma, float(qc), t)
            if e and (best is None or e["per_period_value"] > best["per_period_value"] + 1e-12):
                best = {"qc": float(qc), "t": t, "alpha": e["alpha"], "per_period_value": e["per_period_value"], "war_share": e["war_share"],
                        "long_run_profit": e["long_run_profit"]}
    return best


def main():
    t0 = time.time()
    cells = {}
    for d in C.TABLE_DELTAS:
        for s in C.TABLE_SIGMAS:
            cells[f"{d}|{s}"] = best_cell(d, s)
            print(f"δ = {d}, σ = {s}: {cells[f'{d}|{s}'] and round(cells[f'{d}|{s}']['per_period_value'], 3)}  ({time.time() - t0:.0f} s)", flush=True)
    (ROOT / "gpo_data.json").write_text(json.dumps({"cells": cells, "deltas": C.TABLE_DELTAS, "sigmas": C.TABLE_SIGMAS}, indent=1), encoding="utf-8")
    print("geschrieben")


if __name__ == "__main__":
    main()
