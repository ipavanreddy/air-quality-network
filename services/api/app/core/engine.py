"""Evidence fusion on the H3 grid -> Hotspot Confidence -> hotspots -> action brief -> alert routing.

Pipeline (PRD §32): new evidence -> grid cell context -> validation -> Gemini (photo) ->
deterministic Hotspot Confidence -> forecast -> Gemini brief -> validation -> jurisdiction routing.
"""
import math
import uuid
from datetime import datetime, timedelta

import h3

from app.ai import services as ai
from app.core.samples import age_minutes, now
from app.core.store import Store
from app.forecasting.model import aqi_category, forecast
from app.geospatial_gee.provider import land_use, layers
from app.hotspots import confidence as hc
from app.interop.adapters import (
    StateConfig,
    config_for_jurisdiction,
    configs,
    get_config,
)
from app.sensors_calibration.provider import (
    latest_by_sensor,
    lowcost_observations,
    official_station,
)

H3_RES = 8
GRID_K = 3
SENSOR_RADIUS_KM = 1.2
REPORT_WINDOW_H = 12
PILOT_RADIUS_KM = 150


def dist_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def iso_now() -> str:
    return now().isoformat()


class Engine:
    def __init__(self, store: Store):
        self.store = store

    # ---------------------------------------------------------------- context
    def context(self, cid: str) -> dict:
        cfg = get_config(cid)
        center = h3.latlng_to_cell(*cfg.center, H3_RES)
        cells = sorted(h3.grid_disk(center, GRID_K))
        ingested = [o for o in self.store.all("observations") if o["state"] == cid]
        obs = lowcost_observations(cfg, ingested)
        return {
            "cfg": cfg,
            "center": center,
            "cells": cells,
            "observations": obs,
            "latest": latest_by_sensor(obs),
            "station": official_station(cfg),
            "geo": layers(cfg, cells),
            "land_use": land_use(cfg),
        }

    def nearest_config(self, lat: float, lon: float) -> tuple[StateConfig | None, float]:
        best = min(configs().values(), key=lambda c: dist_km((lat, lon), c.center))
        d = dist_km((lat, lon), best.center)
        return (best if d <= PILOT_RADIUS_KM else None), d

    # ---------------------------------------------------------------- per-cell evidence
    def cell_sensor(self, ctx: dict, cell: str) -> dict | None:
        lat, lon = h3.cell_to_latlng(cell)
        near = []
        for o in ctx["latest"].values():
            d = dist_km((lat, lon), (o["lat"], o["lon"]))
            if d <= SENSOR_RADIUS_KM:
                near.append((max(d, 0.2), o))
        if not near:
            return None
        wsum = sum(1 / d**2 for d, _ in near)
        pm25 = sum(o["pm25_calibrated"] / d**2 for d, o in near) / wsum
        pm10s = [(d, o) for d, o in near if o.get("pm10") is not None]
        pm10 = sum(o["pm10"] / d**2 for d, o in pm10s) / sum(1 / d**2 for d, _ in pm10s) if pm10s else None
        ids = {o["sensor_id"] for _, o in near}
        day = [o["pm25_calibrated"] for o in ctx["observations"] if o["sensor_id"] in ids
               and age_minutes(o["timestamp"]) is not None and age_minutes(o["timestamp"]) <= 24 * 60]
        st = ctx["station"]
        return {
            "pm25_calibrated": round(pm25, 1),
            "pm10": round(pm10, 1) if pm10 is not None else None,
            "pm25_24h_mean": round(sum(day) / len(day), 1) if day else round(pm25, 1),
            "expected_pm25": st.get("pm25"),
            "expected_pm10": st.get("pm10"),
            "station_name": st.get("name"),
            "station_distance_km": round(dist_km((lat, lon), (st["lat"], st["lon"])), 1),
            "sensors_used": sorted(ids),
            "source": "Low-cost sensors, humidity-calibrated (indicative)"
                      + (" - SIMULATED" if any(o["is_simulated"] for _, o in near) else ""),
            "observed_at": max(o["timestamp"] for _, o in near),
            "indicative": True,
            "calibration_model_version": near[0][1]["calibration_model_version"],
        }

    def upwind(self, ctx: dict, cell: str) -> tuple[bool, list[str]]:
        wx = ctx["geo"]["weather"]["current"]
        lu = ctx["land_use"]
        lat, lon = h3.cell_to_latlng(cell)
        found = []
        for other in h3.grid_disk(cell, 3):
            if other == cell or lu.get(other) not in hc.SOURCE_LAND_USES:
                continue
            olat, olon = h3.cell_to_latlng(other)
            if hc.angle_diff(hc.bearing_deg(lat, lon, olat, olon), wx["wind_dir_deg"]) <= 45:
                found.append(lu[other])
        sat = ctx["geo"]["satellite"].get(cell) or {}
        consistent = (lu.get(cell) in hc.SOURCE_LAND_USES or bool(found)
                      or (sat.get("fire_count_upwind_100km") or 0) >= 5)
        return consistent, sorted(set(found))

    def reports_near(self, cid: str, cell: str) -> list[dict]:
        cutoff = now() - timedelta(hours=REPORT_WINDOW_H)
        out = []
        for r in self.store.all("reports"):
            v = r.get("verification") or {}
            if r["state"] != cid or not v.get("is_pollution_event") or r["status"] == "rejected":
                continue
            if datetime.fromisoformat(r["created_at"]) < cutoff:
                continue
            ring = h3.grid_distance(cell, r["h3_cell"]) if h3.is_valid_cell(r["h3_cell"]) else 99
            if ring <= 2:
                out.append({**r, "_ring": ring})
        return out

    def score_cell(self, ctx: dict, cell: str, reports: list[dict] | None = None) -> dict:
        cid = ctx["cfg"].id
        sensor = self.cell_sensor(ctx, cell)
        sat = ctx["geo"]["satellite"].get(cell) or {}
        wx = ctx["geo"]["weather"]["current"]
        consistent, _ = self.upwind(ctx, cell)
        reports = self.reports_near(cid, cell) if reports is None else reports
        factors = [
            hc.sensor_anomaly(sensor and sensor["pm25_calibrated"], sensor and sensor["expected_pm25"],
                              sensor and sensor["pm10"], sensor and sensor["expected_pm10"]),
            hc.satellite(sat.get("no2_column_anomaly_pct"), sat.get("fire_count_upwind_100km"), sat.get("aod")),
            hc.citizen_reports([(r["verification"]["confidence"], r["verification"]["visual_severity"], r["_ring"])
                                for r in reports]),
            hc.weather(wx.get("wind_speed_ms"), wx.get("boundary_layer_m"), consistent),
        ]
        return {**hc.combine(factors), "sensor": sensor, "report_ids": [r["report_id"] for r in reports]}

    # ---------------------------------------------------------------- grid
    def grid(self, cid: str) -> dict:
        ctx = self.context(cid)
        cfg = ctx["cfg"]
        hotspot_by_cell = {c: h["hotspot_id"] for h in self.store.all("hotspots")
                           if h["state"] == cid and h["status"] != "closed" for c in h["h3_cells"]}
        cells = []
        for cell in ctx["cells"]:
            s = self.score_cell(ctx, cell)
            lat, lon = h3.cell_to_latlng(cell)
            pm = s["sensor"]["pm25_calibrated"] if s["sensor"] else None
            cells.append({
                "h3_cell": cell,
                "lat": lat,
                "lon": lon,
                "boundary": [list(p) for p in h3.cell_to_boundary(cell)],
                "pm25": pm,
                "category": aqi_category(pm) if pm is not None else None,
                "confidence": s["confidence"],
                "band": s["band"],
                "land_use": ctx["land_use"].get(cell),
                "report_count": len(s["report_ids"]),
                "fire_count_upwind_100km": (ctx["geo"]["satellite"].get(cell) or {}).get("fire_count_upwind_100km"),
                "hotspot_id": hotspot_by_cell.get(cell),
            })
        return {
            "state": cid,
            "name": cfg.name,
            "center": cfg.center,
            "threshold": cfg.hotspot_threshold,
            "cells": cells,
            "sensors": list(ctx["latest"].values()),
            "station": ctx["station"],
            "weather": ctx["geo"]["weather"]["current"],
            "freshness": self.freshness(ctx),
            "is_sample_data": self.is_sample(ctx),
        }

    def is_sample(self, ctx: dict) -> bool:
        return bool(ctx["station"].get("is_sample") or ctx["geo"]["meta"]["mode"] == "sample"
                    or any(o["is_simulated"] for o in ctx["latest"].values()))

    def freshness(self, ctx: dict) -> list[dict]:
        latest = list(ctx["latest"].values())
        sat = next(iter(ctx["geo"]["satellite"].values()), {})
        wx = ctx["geo"]["weather"]
        st = ctx["station"]
        items = [
            ("Low-cost sensors (calibrated, indicative)", max((o["timestamp"] for o in latest), default=None),
             "Simulated low-cost feed" if any(o["is_simulated"] for o in latest) else "Community sensors",
             any(o["is_simulated"] for o in latest)),
            ("Official station", st.get("observed_at"), st.get("source"), st.get("is_sample", False)),
            ("Satellite NO2", sat.get("no2_observed_at"), sat.get("no2_source"), sat.get("is_sample", False)),
            ("Aerosol optical depth", sat.get("aod_observed_at"), sat.get("aod_source"), sat.get("is_sample", False)),
            ("Fire detections", sat.get("fire_observed_at"), sat.get("fire_source"), sat.get("is_sample", False)),
            ("Weather (current)", wx["current"].get("observed_at"), wx["current"].get("source"),
             wx["current"].get("is_sample", False)),
            ("Weather forecast (issued)", wx["forecast"].get("issued_at"), wx["forecast"].get("source"),
             wx["forecast"].get("is_sample", False)),
        ]
        return [{"signal": s, "observed_at": t, "age_minutes": age_minutes(t), "source": src, "is_sample": smp}
                for s, t, src, smp in items]

    # ---------------------------------------------------------------- forecast
    def cell_forecast(self, cid: str, cell: str, ctx: dict | None = None) -> dict:
        ctx = ctx or self.context(cid)
        cfg = ctx["cfg"]
        sensor = self.cell_sensor(ctx, cell)
        pm_now = sensor["pm25_24h_mean"] if sensor else ctx["station"]["pm25"]
        fc = forecast(cfg.id, cfg.forecast_model, pm_now, ctx["geo"]["weather"]["forecast"]["steps"])
        return {**fc, "location_id": cell, "issued_at": iso_now(),
                "basis": "24h mean of nearby calibrated sensors" if sensor else "official station",
                "is_sample_data": self.is_sample(ctx)}

    def corridor_forecast(self, cid: str) -> dict:
        ctx = self.context(cid)
        cfg = ctx["cfg"]
        day = [o["pm25_calibrated"] for o in ctx["observations"]
               if (age_minutes(o["timestamp"]) or 0) <= 24 * 60]
        pm_now = sum(day) / len(day) if day else ctx["station"]["pm25"]
        fc = forecast(cfg.id, cfg.forecast_model, pm_now, ctx["geo"]["weather"]["forecast"]["steps"])
        return {**fc, "location_id": cfg.corridor, "state": cid, "issued_at": iso_now(),
                "basis": "24h mean of corridor sensors (calibrated)", "is_sample_data": self.is_sample(ctx)}

    # ---------------------------------------------------------------- evidence bundle
    def bundle(self, ctx: dict, hotspot: dict) -> dict:
        cfg = ctx["cfg"]
        cell = hotspot["peak_cell"]
        s = self.score_cell(ctx, cell)
        sat = {k: v for k, v in (ctx["geo"]["satellite"].get(cell) or {}).items() if k not in ("state",)}
        _, upwind_uses = self.upwind(ctx, cell)
        lat, lon = h3.cell_to_latlng(cell)
        reports = [{"report_id": r["report_id"], "source_type": r["verification"]["source_type"],
                    "confidence": r["verification"]["confidence"],
                    "visual_severity": r["verification"]["visual_severity"],
                    "observed_indicators": r["verification"]["observed_indicators"],
                    "created_at": r["created_at"], "ring_distance": r["_ring"],
                    "requires_human_review": r["verification"]["requires_human_review"]}
                   for r in self.reports_near(cfg.id, cell)]
        return {
            "area": f"{cfg.corridor}, {cfg.name}",
            "hotspot": {"hotspot_id": hotspot["hotspot_id"], "h3_cells": hotspot["h3_cells"], "peak_cell": cell,
                        "confidence": s["confidence"], "band": s["band"], "factors": s["factors"],
                        "fast_path": hotspot.get("fast_path", False)},
            "cell": {"h3_cell": cell, "lat": round(lat, 5), "lon": round(lon, 5)},
            "sensor": s["sensor"],
            "satellite": sat,
            "weather": ctx["geo"]["weather"]["current"],
            "land_use": {"cell_land_use": ctx["land_use"].get(cell), "upwind_land_uses": upwind_uses,
                         "source": "Synthetic demo land-use labels"},
            "citizen_reports": reports,
            "forecast": self.cell_forecast(cfg.id, cell, ctx),
            "data_freshness": self.freshness(ctx),
            "is_sample_data": self.is_sample(ctx),
        }

    # ---------------------------------------------------------------- detection
    def detect(self, cid: str) -> list[dict]:
        """Recompute hotspots for a state; create briefs + alerts for new ones. Returns touched hotspots."""
        ctx = self.context(cid)
        cfg = ctx["cfg"]
        scores = {cell: self.score_cell(ctx, cell) for cell in ctx["cells"]}
        fast = set()
        fp = cfg.fast_path
        for cell in ctx["cells"]:
            for r in self.reports_near(cid, cell):
                v = r["verification"]
                if (r["_ring"] == 0 and v["visual_severity"] >= fp["min_visual_severity"]
                        and v["confidence"] >= fp["min_confidence"]):
                    fast.add(cell)
        candidates = {c for c, s in scores.items() if s["confidence"] >= cfg.hotspot_threshold} | fast
        components = self._components(candidates)
        existing = [h for h in self.store.all("hotspots") if h["state"] == cid and h["status"] != "closed"]
        touched = []
        for comp in components:
            peak = max(comp, key=lambda c: scores[c]["confidence"])
            match = next((h for h in existing if set(h["h3_cells"]) & comp), None)
            s = scores[peak]
            hs = match or {
                "hotspot_id": self._next_id("hotspots", "HS", cfg.state_code),
                "state": cid,
                "detected_at": iso_now(),
                "status": "active",
                "jurisdiction_id": cfg.jurisdiction.id,
                "brief": None,
                "alert_id": None,
            }
            hs.update({
                "h3_cells": sorted(comp),
                "peak_cell": peak,
                "center": list(h3.cell_to_latlng(peak)),
                "confidence": s["confidence"],
                "band": s["band"],
                "factors": s["factors"],
                "evidence_types": s["evidence_types"],
                "fast_path": bool(comp & fast) and s["confidence"] < cfg.hotspot_threshold,
                "threshold": cfg.hotspot_threshold,
                "updated_at": iso_now(),
                "report_ids": sorted({rid for c in comp for rid in scores[c]["report_ids"]}),
                "is_sample_data": self.is_sample(ctx),
            })
            if hs["brief"] is None:
                self._attach_brief(ctx, hs)
            self.store.put("hotspots", hs["hotspot_id"], hs)
            if hs["alert_id"] is None:
                self._create_alert(ctx, hs)
            touched.append(hs)
        return touched

    @staticmethod
    def _components(cells: set[str]) -> list[set[str]]:
        comps, seen = [], set()
        for c in sorted(cells):
            if c in seen:
                continue
            comp, stack = set(), [c]
            while stack:
                x = stack.pop()
                if x in comp:
                    continue
                comp.add(x)
                stack.extend(n for n in h3.grid_ring(x, 1) if n in cells and n not in comp)
            seen |= comp
            comps.append(comp)
        return comps

    @staticmethod
    def _next_id(collection: str, prefix: str, code: str) -> str:
        return f"{prefix}-{code}-{uuid.uuid4().hex[:6].upper()}"

    def _attach_brief(self, ctx: dict, hs: dict) -> None:
        cfg = ctx["cfg"]
        bundle = self.bundle(ctx, hs)
        brief, prov = ai.action_brief(bundle, [r.model_dump() for r in cfg.action_rules], cfg.jurisdiction.name)
        hs["brief"] = brief.model_dump()
        hs["brief_provenance"] = prov
        hs["likely_sources"] = hs["brief"]["likely_sources"]
        hs["model_name"], hs["model_version"], hs["prompt_version"] = (
            prov["model_name"], prov["model_version"], prov["prompt_version"])
        hs["cross_boundary"] = self._cross_boundary(ctx, hs)

    def regenerate_brief(self, hotspot_id: str) -> dict:
        hs = self.store.get("hotspots", hotspot_id)
        if hs is None:
            raise KeyError(hotspot_id)
        ctx = self.context(hs["state"])
        self._attach_brief(ctx, hs)
        self.store.put("hotspots", hotspot_id, hs)
        alert = self.store.get("alerts", hs["alert_id"]) if hs.get("alert_id") else None
        if alert and alert["status"] == "pending_review":
            self._copy_brief(alert, hs)
            self._event(alert, "system", "brief_regenerated", "Action brief regenerated")
            self.store.put("alerts", alert["alert_id"], alert)
        return hs

    def _cross_boundary(self, ctx: dict, hs: dict) -> dict | None:
        cfg = ctx["cfg"]
        wx = ctx["geo"]["weather"]["current"]
        top = hs["likely_sources"][0]["type"] if hs.get("likely_sources") else None
        for nb in cfg.cross_boundary_neighbours:
            lat, lon = hs["center"]
            bearing = hc.bearing_deg(lat, lon, *nb.center)
            wind_to = (wx["wind_dir_deg"] + 180) % 360
            if hc.angle_diff(bearing, wind_to) <= 45 and top in nb.sources:
                d = dist_km((lat, lon), nb.center)
                eta = d / max(wx["wind_speed_ms"] * 3.6, 0.5)
                return {"target_config": nb.config_id, "target_jurisdiction_id": nb.jurisdiction_id,
                        "target_name": nb.name, "distance_km": round(d), "bearing_deg": round(bearing),
                        "wind_to_deg": round(wind_to), "eta_hours": round(eta),
                        "reason": f"Wind blowing toward {nb.name} ({round(wind_to)} deg) and likely "
                                  f"source is {top.replace('_', ' ')}"}
        return None

    # ---------------------------------------------------------------- alerts
    @staticmethod
    def _event(alert: dict, actor: str, event: str, note: str = "") -> None:
        alert.setdefault("history", []).append({"at": iso_now(), "actor": actor, "event": event, "note": note})

    @staticmethod
    def _copy_brief(alert: dict, hs: dict) -> None:
        prov = hs["brief_provenance"]
        alert.update({"action_brief": hs["brief"], "brief_provenance": prov, "model_name": prov["model_name"],
                      "model_version": prov["model_version"], "prompt_version": prov["prompt_version"],
                      "cross_boundary_suggestion": hs.get("cross_boundary")})

    def _create_alert(self, ctx: dict, hs: dict) -> dict:
        cfg = ctx["cfg"]
        alert = {
            "alert_id": self._next_id("alerts", "AL", cfg.state_code),
            "kind": "hotspot",
            "hotspot_id": hs["hotspot_id"],
            "state": cfg.id,
            "jurisdiction_id": cfg.jurisdiction.id,
            "jurisdiction_name": cfg.jurisdiction.name,
            "origin_jurisdiction_id": None,
            "sent_at": iso_now(),
            "status": "pending_review",
            "confidence": hs["confidence"],
            "band": hs["band"],
            "fast_path": hs["fast_path"],
            "acknowledged_at": None,
            "acknowledged_by": None,
            "approved_action_ids": [],
            "action_taken": None,
            "action_taken_at": None,
            "closed_at": None,
            "resolution": None,
            "language": cfg.default_language,
            "cross_boundary_alert_id": None,
            "is_sample_data": hs["is_sample_data"],
        }
        self._copy_brief(alert, hs)
        route = "fast path (severe visible event)" if hs["fast_path"] else \
            f"confidence {hs['confidence']:.0f} >= threshold {cfg.hotspot_threshold:.0f}"
        self._event(alert, "system", "routed", f"Routed to {cfg.jurisdiction.id} by jurisdiction lookup; {route}")
        hs["alert_id"] = alert["alert_id"]
        self.store.put("hotspots", hs["hotspot_id"], hs)
        return self.store.put("alerts", alert["alert_id"], alert)

    def _alert(self, alert_id: str) -> dict:
        a = self.store.get("alerts", alert_id)
        if a is None:
            raise KeyError(alert_id)
        return a

    def acknowledge(self, alert_id: str, officer: str, approved_action_ids: list[str], note: str = "") -> dict:
        a = self._alert(alert_id)
        if a["status"] != "pending_review":
            raise ValueError(f"alert is {a['status']}")
        valid = {x["action_id"] for x in a["action_brief"]["recommended_actions"]}
        a.update({"status": "acknowledged", "acknowledged_at": iso_now(), "acknowledged_by": officer,
                  "approved_action_ids": [x for x in approved_action_ids if x in valid]})
        self._event(a, officer, "acknowledged",
                    f"Approved actions: {', '.join(a['approved_action_ids']) or 'none'}. {note}".strip())
        return self.store.put("alerts", alert_id, a)

    def record_action(self, alert_id: str, officer: str, action_taken: str) -> dict:
        a = self._alert(alert_id)
        if a["status"] not in ("acknowledged", "action_taken"):
            raise ValueError("acknowledge the alert before recording an action")
        a.update({"status": "action_taken", "action_taken": action_taken, "action_taken_at": iso_now()})
        self._event(a, officer, "action_taken", action_taken)
        return self.store.put("alerts", alert_id, a)

    def close(self, alert_id: str, officer: str, resolution: str) -> dict:
        a = self._alert(alert_id)
        if a["status"] == "pending_review":
            raise ValueError("acknowledge the alert before closing it")
        a.update({"status": "closed", "closed_at": iso_now(), "resolution": resolution})
        self._event(a, officer, "closed", resolution)
        hs = self.store.get("hotspots", a["hotspot_id"]) if a.get("hotspot_id") else None
        if hs and a["kind"] == "hotspot":
            hs["status"] = "closed"
            self.store.put("hotspots", hs["hotspot_id"], hs)
        return self.store.put("alerts", alert_id, a)

    def send_cross_boundary(self, alert_id: str, officer: str, note: str = "") -> dict:
        """Officer-approved transfer of a hotspot alert to the downwind jurisdiction (PRD §43 B)."""
        a = self._alert(alert_id)
        sug = a.get("cross_boundary_suggestion")
        if not sug:
            raise ValueError("no cross-boundary impact suggested for this alert")
        if a.get("cross_boundary_alert_id"):
            raise ValueError("cross-boundary alert already sent")
        if a["status"] == "pending_review":
            raise ValueError("acknowledge (approve) the alert before sending it across the boundary")
        target = get_config(sug["target_config"])
        origin = config_for_jurisdiction(a["jurisdiction_id"])
        hs = self.store.get("hotspots", a["hotspot_id"])
        rules = [r for r in target.action_rules
                 if "crop_residue_burning" in r.applies_to or "*" in r.applies_to]
        brief = dict(a["action_brief"])
        brief.update({
            "summary": (f"Incoming smoke: likely {hs['likely_sources'][0]['type'].replace('_', ' ')} in "
                        f"{origin.city}, {origin.name} (~{sug['distance_km']} km upwind). Wind carries it toward "
                        f"{target.name}; estimated arrival ~{sug['eta_hours']} h. Forwarded by {origin.jurisdiction.id} "
                        f"after officer approval."),
            "recommended_actions": [{"action_id": r.id, "action": r.action, "priority": "high" if i == 0 else "medium"}
                                    for i, r in enumerate(rules[:3])],
            "requires_human_review": True,
        })
        xa = {
            **{k: None for k in ("acknowledged_at", "acknowledged_by", "action_taken", "action_taken_at",
                                 "closed_at", "resolution", "cross_boundary_alert_id", "cross_boundary_suggestion")},
            "alert_id": self._next_id("alerts", "AL", target.state_code),
            "kind": "cross_boundary",
            "hotspot_id": a["hotspot_id"],
            "state": target.id,
            "jurisdiction_id": target.jurisdiction.id,
            "jurisdiction_name": target.jurisdiction.name,
            "origin_jurisdiction_id": a["jurisdiction_id"],
            "origin_alert_id": alert_id,
            "sent_at": iso_now(),
            "status": "pending_review",
            "confidence": a["confidence"],
            "band": a["band"],
            "fast_path": False,
            "approved_action_ids": [],
            "language": target.default_language,
            "action_brief": brief,
            "brief_provenance": {**a["brief_provenance"],
                                 "note": "Derived from origin alert brief; summary/actions re-targeted by rules"},
            "model_name": a["model_name"], "model_version": a["model_version"], "prompt_version": a["prompt_version"],
            "cross_boundary": sug,
            "is_sample_data": a["is_sample_data"],
        }
        self._event(xa, officer, "routed", f"Cross-boundary alert from {a['jurisdiction_id']} approved by {officer}. "
                                           f"{note}".strip())
        self.store.put("alerts", xa["alert_id"], xa)
        a["cross_boundary_alert_id"] = xa["alert_id"]
        self._event(a, officer, "cross_boundary_sent", f"Sent to {target.jurisdiction.id} as {xa['alert_id']}")
        self.store.put("alerts", alert_id, a)
        return xa

    # ---------------------------------------------------------------- advisories
    def generate_advisory(self, cid: str, cell: str | None = None) -> dict:
        ctx = self.context(cid)
        cfg = ctx["cfg"]
        cell = cell or ctx["center"]
        fc = self.cell_forecast(cid, cell, ctx)
        sensor = self.cell_sensor(ctx, cell)
        pm_now = sensor["pm25_calibrated"] if sensor else ctx["station"]["pm25"]
        context = {
            "place": cfg.corridor.split(" corridor")[0] if cfg.id == "delhi-ncr" else cfg.city,
            "pm25_now": round(pm_now),
            "category_now": aqi_category(pm_now),
            "forecast": [{"horizon_hours": h["horizon_hours"], "category": h["category"],
                          "pm25_expected": h["pm25_expected"]} for h in fc["horizons"]],
            "audience": "general public and sensitive groups",
            "data_note": "Local values from calibrated low-cost sensors are indicative",
        }
        base, prov = ai.health_advisory(context)
        translations = {}
        for lang in ("en", "hi", "pa"):
            text, meta = ai.translate_advisory(base, lang, context, prov["mode"])
            translations[lang] = {**text, "translation": meta}
        adv = {
            "advisory_id": f"AD-{cfg.state_code}-{uuid.uuid4().hex[:6]}",
            "state": cid,
            "h3_cell": cell,
            "category": context["category_now"],
            "context": context,
            "base": base.model_dump(),
            "translations": translations,
            "default_language": cfg.default_language,
            "status": "draft",
            "created_at": iso_now(),
            "approved_by": None,
            "approved_at": None,
            "provenance": prov,
            "model_name": prov["model_name"], "model_version": prov["model_version"],
            "prompt_version": prov["prompt_version"],
            "is_sample_data": self.is_sample(ctx),
        }
        return self.store.put("advisories", adv["advisory_id"], adv)

    def approve_advisory(self, advisory_id: str, officer: str) -> dict:
        adv = self.store.get("advisories", advisory_id)
        if adv is None:
            raise KeyError(advisory_id)
        adv.update({"status": "approved", "approved_by": officer, "approved_at": iso_now()})
        return self.store.put("advisories", advisory_id, adv)

