"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

# Nachfrage: Preis p = θ · (A − Q) mit Gesamtmenge Q und lognormalem Schock θ (Erwartung 1); Grenzkosten C je Einheit; zwei Anbieter.
A, C = 10.0, 1.0
Q_MONOPOLY = (A - C) / 2.0                    # Gesamtmenge des Monopols: 4,5
Q_COURNOT = 2.0 * (A - C) / 3.0               # Gesamtmenge des Cournot-Duopols: 6,0

DELTA_MIN, DELTA_MAX, DEFAULT_DELTA, DELTA_STEP = 0.50, 0.97, 0.90, 0.01
SIGMA_MIN, SIGMA_MAX, DEFAULT_SIGMA, SIGMA_STEP = 0.05, 0.60, 0.10, 0.05
QC_MIN, QC_MAX, DEFAULT_QC, QC_STEP = Q_MONOPOLY, Q_COURNOT, 5.3, 0.05
T_MIN, T_MAX, DEFAULT_T, T_STEP = 1, 40, 30, 1
SEED_MAX, DEFAULT_SEED = 999999, 20266
SIM_STEPS = 400                               # Perioden der gezeigten Preisreihe

QC_GRID = tuple(round(4.5 + 0.1 * i, 1) for i in range(0, 16))      # 4,5 bis 6,0
T_GRID = (1, 2, 3, 5, 8, 12, 20, 30, 40)
DEVIATION_GRID_N = 400
TOL = 1e-9

TABLE_DELTAS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
TABLE_SIGMAS = (0.05, 0.1, 0.15, 0.2, 0.3, 0.5)

COLOR_COLLUSION = "#2F6B65"
COLOR_WAR = "#B5483A"
COLOR_DEVIATION = "#e08a2c"
COLOR_LINE = "#4c78a8"
COLOR_OTHER = "rgba(150,150,150,0.55)"

PRESETS = {
    "Voreinstellung (δ = 0,90, σ = 0,10)": {"delta": 0.90, "sigma": 0.10, "qc": 5.3, "t": 30},
    "Kurze Strafphase (T = 3)": {"delta": 0.90, "sigma": 0.10, "qc": 5.3, "t": 3},
    "Engere Absprache (Menge 4,8)": {"delta": 0.90, "sigma": 0.10, "qc": 4.8, "t": 30},
    "Sehr geduldig (δ = 0,97)": {"delta": 0.97, "sigma": 0.10, "qc": 5.0, "t": 30},
    "Sehr verrauschter Markt (σ = 0,50)": {"delta": 0.90, "sigma": 0.50, "qc": 5.3, "t": 30},
}
PRESET_HELP = {
    "Voreinstellung (δ = 0,90, σ = 0,10)": "Ruhiger Markt, geduldige Anbieter: Absprache mit langer Strafphase ist ein Gleichgewicht, und Preiskriege treten regelmäßig auf, ohne dass jemand abweicht.",
    "Kurze Strafphase (T = 3)": "Drei Perioden Krieg schrecken nicht genug ab: bei dieser Menge gibt es keine tragbare Absprache.",
    "Engere Absprache (Menge 4,8)": "Näher an der Monopolmenge: das Gleichgewicht braucht häufigere Kriege (rund 80 % der Zeit) und bringt wenig mehr.",
    "Sehr geduldig (δ = 0,97)": "Mit sehr geduldigen Anbietern trägt eine engere Absprache bei kleinerer Auslösewahrscheinlichkeit.",
    "Sehr verrauschter Markt (σ = 0,50)": "Bei viel Rauschen kann der Preis Abweichen nicht mehr vom Zufall unterscheiden: keine Absprache ist tragbar.",
}
