"""Corridor PM2.5 forecast (PRD §15, FR-07) and the shared regional model (PRD §19).

`igp-smog-forecast-v1` is a small linear model per horizon (24/48/72 h):
    pm25[t+h] = b0 + b1 * pm25[t] + b2 * ventilation_index[t+h]/1000 + b3 * upwind_fires[t+h]
trained on the pooled Delhi NCR + Punjab (Indo-Gangetic Plain) standardised features, then
"fine-tuned" per configuration with a bias offset on that configuration's own data. Accuracy vs a
persistence baseline is backtested on the last 20 days and published in the model card.
Maharashtra uses `persistence-baseline-v1` to show a configuration with a different model.
The training data are the committed SIMULATED histories (data/sample/<state>/pm25_history_daily.json).
A Vertex AI forecasting model can replace this behind `forecast()`.
"""
import math
from functools import lru_cache

from app.core.samples import load

HORIZONS = (24, 48, 72)
TEST_DAYS = 20
SHARED_MODEL = "igp-smog-forecast-v1"
PERSISTENCE = "persistence-baseline-v1"
SHARED_TRAIN_CONFIGS = ("delhi-ncr", "punjab")


def aqi_category(pm25: float) -> str:
    """India National AQI sub-index category for 24 h PM2.5 (ug/m3)."""
    for limit, name in ((30, "Good"), (60, "Satisfactory"), (90, "Moderate"), (120, "Poor"),
                        (250, "Very Poor")):
        if pm25 <= limit:
            return name
    return "Severe"


def _history(config_id: str) -> list[dict]:
    return load(f"{config_id}/pm25_history_daily.json", replay=False)["records"]


def _rows(hist: list[dict], days: int) -> list[tuple[list[float], float, float, bool]]:
    rows = []
    for i in range(len(hist) - days):
        tgt = hist[i + days]
        x = [1.0, hist[i]["pm25"], tgt["ventilation_index_m2s"] / 1000, float(tgt["fire_count"])]
        is_test = i + days >= len(hist) - TEST_DAYS
        rows.append((x, tgt["pm25"], hist[i]["pm25"], is_test))
    return rows


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        if abs(m[c][c]) < 1e-12:
            m[c][c] = 1e-12
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                m[r] = [m[r][k] - f * m[c][k] for k in range(n + 1)]
    return [m[i][n] / m[i][i] for i in range(n)]


def _fit(rows) -> list[float]:
    k = len(rows[0][0])
    xtx = [[sum(r[0][i] * r[0][j] for r in rows) + (1e-6 if i == j else 0) for j in range(k)] for i in range(k)]
    xty = [sum(r[0][i] * r[1] for r in rows) for i in range(k)]
    return _solve(xtx, xty)


def _pred(coef, x) -> float:
    return sum(c * v for c, v in zip(coef, x))


def _mae(pairs) -> float:
    return round(sum(abs(a - b) for a, b in pairs) / len(pairs), 1) if pairs else 0.0


@lru_cache
def trained() -> dict:
    """Fit the shared model and compute per-config fine-tune offsets + backtest metrics."""
    models: dict = {"coef": {}, "sigma": {}, "bias": {}, "metrics": {}}
    for h in HORIZONS:
        days = h // 24
        pooled = [r for cid in SHARED_TRAIN_CONFIGS for r in _rows(_history(cid), days) if not r[3]]
        coef = _fit(pooled)
        models["coef"][h] = coef
        resid = [r[1] - _pred(coef, r[0]) for r in pooled]
        models["sigma"][h] = math.sqrt(sum(e * e for e in resid) / len(resid))
    for cid in ("delhi-ncr", "punjab", "maharashtra"):
        hist = _history(cid)
        models["bias"][cid] = {}
        models["metrics"][cid] = {}
        for h in HORIZONS:
            rows = _rows(hist, h // 24)
            train = [r for r in rows if not r[3]]
            test = [r for r in rows if r[3]]
            coef = models["coef"][h]
            bias = sum(r[1] - _pred(coef, r[0]) for r in train) / len(train)
            models["bias"][cid][h] = bias
            models["metrics"][cid][h] = {
                "model_mae": _mae([(r[1], _pred(coef, r[0]) + bias) for r in test]),
                "persistence_mae": _mae([(r[1], r[2]) for r in test]),
                "persistence_sigma": math.sqrt(sum((r[1] - r[2]) ** 2 for r in train) / len(train)),
                "test_days": len(test),
            }
    return models


def _drivers(step: dict, pm_now: float, expected: float) -> list[str]:
    out = []
    vi = step.get("ventilation_index_m2s")
    if vi is not None and vi < 600:
        out.append(f"poor ventilation (index ~{vi:.0f} m2/s): calm winds / shallow mixing layer")
    elif vi is not None and vi > 1200:
        out.append(f"good ventilation (index ~{vi:.0f} m2/s) helps dispersion")
    fires = step.get("fire_count_upwind_forecast")
    if fires:
        out.append(f"upwind fire activity (~{fires} detections expected)")
    if step.get("rain_mm"):
        out.append(f"rain ({step['rain_mm']} mm) may wash out particles")
    out.append("rising trend" if expected > pm_now * 1.05 else "easing trend" if expected < pm_now * 0.95
               else "similar to today (persistence)")
    return out


def forecast(config_id: str, model_id: str, pm_now: float, steps: list[dict]) -> dict:
    m = trained()
    out = []
    for step in steps:
        h = step["horizon_hours"]
        if model_id == SHARED_MODEL:
            x = [1.0, pm_now, (step.get("ventilation_index_m2s") or 800) / 1000,
                 float(step.get("fire_count_upwind_forecast") or 0)]
            expected = _pred(m["coef"][h], x) + m["bias"][config_id][h]
            sigma = m["sigma"][h]
        else:
            expected = pm_now
            sigma = m["metrics"][config_id][h]["persistence_sigma"]
        expected = max(5.0, expected)
        out.append({
            "horizon_hours": h,
            "pm25_low": round(max(0.0, expected - 1.28 * sigma)),
            "pm25_expected": round(expected),
            "pm25_high": round(expected + 1.28 * sigma),
            "category": aqi_category(expected),
            "drivers": _drivers(step, pm_now, expected),
        })
    return {"model_id": model_id, "model_version": model_id, "pm25_now": round(pm_now),
            "category_now": aqi_category(pm_now), "horizons": out}
