"""Low-cost sensor humidity correction (PRD §10; Priority 4 'simple correction').

Optical low-cost PM sensors over-read in humid air because particles absorb water. We apply the
kappa-Kohler style correction used in the literature (e.g. Crilley et al., 2018, AMT):

    pm25_calibrated = pm25_raw / (1 + (kappa / 1.65) / (1/RH - 1))

with a fixed kappa. Calibrated low-cost values are always labelled *indicative*.
A trained co-location model (Vertex AI / BigQuery ML) can replace this behind the same function.
"""

CALIBRATION_MODEL_VERSION = "lowcost-humidity-calibration-v1"
KAPPA = 0.3


def growth_factor(humidity_pct: float | None) -> float:
    if humidity_pct is None:
        return 1.0
    rh = min(max(humidity_pct, 1.0), 95.0) / 100
    return 1 + (KAPPA / 1.65) / (-1 + 1 / rh)


def calibrate_pm25(pm25_raw: float, humidity_pct: float | None) -> float:
    return round(pm25_raw / growth_factor(humidity_pct), 1)
