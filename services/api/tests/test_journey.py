"""Demo-mode end-to-end journey (PRD §44): citizen photo -> verification -> fusion -> Hotspot
Confidence -> likely source + action brief -> officer alert -> acknowledge -> action -> close,
plus Punjab -> Delhi cross-boundary alert and the multilingual advisory."""
from app.config import settings

PHOTOS = settings.sample_data_dir / "photos"
DELHI = {"lat": "28.628", "lon": "77.295"}


def submit(client, photo: str, where: dict, **extra):
    data = (PHOTOS / photo).read_bytes()
    res = client.post("/api/reports", files={"photo": (photo, data, "image/png")},
                      data={**where, "language": "hi", "reporter_id": "citizen-123", **extra})
    assert res.status_code == 200, res.text
    return res.json()


def test_core_journey_delhi(fresh):
    c = fresh
    # Before the report: evidence is suggestive but below threshold -> no Delhi hotspot yet
    assert c.get("/api/hotspots?city=delhi-ncr").json() == []
    assert c.get("/api/alerts?jurisdiction=DL-DPCC").json() == []

    # 1. Citizen photo -> AI verification (fixture in demo mode)
    report = submit(c, "industrial_smoke_night.png", DELHI, description="Black smoke from chimney at 3am")
    v = report["verification"]
    assert report["status"] == "verified"
    assert v["is_pollution_event"] and v["source_type"] == "industrial_emission" and v["observed_indicators"]
    for k in ("model_name", "model_version", "prompt_version"):
        assert report[k]
    assert c.get(f"/api/reports/{report['report_id']}/photo").status_code == 200

    # 2-3. Fusion on the grid + Hotspot Confidence crosses the threshold because of the report
    impact = report["impact"]
    assert impact["cell_confidence_before"] < impact["threshold"] <= impact["cell_confidence_after"]
    assert impact["hotspot_id"] and impact["alert_id"]
    hs = c.get(f"/api/hotspots/{impact['hotspot_id']}").json()
    assert hs["evidence_types"] >= 4 and len(hs["factors"]) == 4
    assert hs["jurisdiction_id"] == "DL-DPCC"

    # 4. Likely source + action brief, grounded and labelled
    brief = hs["brief"]
    assert brief["likely_sources"][0]["type"] == "industrial_emission"
    assert brief["evidence"] and all(e["source"] and e["observed"] for e in brief["evidence"])
    assert brief["recommended_actions"] and brief["uncertainties"] and brief["requires_human_review"]
    assert "likely" in brief["summary"].lower()
    assert hs["brief_provenance"]["validation_warnings"] == []
    assert hs["brief_provenance"]["mode"] == "demo_fixture"

    # 5. Officer alert with human approval: acknowledge -> action -> close
    alert = c.get(f"/api/alerts/{impact['alert_id']}").json()
    assert alert["status"] == "pending_review" and alert["kind"] == "hotspot"
    first_action = brief["recommended_actions"][0]["action_id"]
    ack = c.post(f"/api/alerts/{alert['alert_id']}/acknowledge",
                 json={"officer": "officer.dl", "approved_action_ids": [first_action, "NOT-A-RULE"]}).json()
    assert ack["status"] == "acknowledged" and ack["approved_action_ids"] == [first_action]
    act = c.post(f"/api/alerts/{alert['alert_id']}/action",
                 json={"officer": "officer.dl", "action_taken": "Night inspection team dispatched"}).json()
    assert act["status"] == "action_taken"
    closed = c.post(f"/api/alerts/{alert['alert_id']}/close",
                    json={"officer": "officer.dl", "resolution": "Unit issued direction"}).json()
    assert closed["status"] == "closed"
    assert [e["event"] for e in closed["history"]] == ["routed", "acknowledged", "action_taken", "closed"]
    assert c.get(f"/api/hotspots/{impact['hotspot_id']}").json()["status"] == "closed"

    # Citizen can see report status
    assert c.get(f"/api/reports/{report['report_id']}").json()["status_timeline"][-1]["event"].startswith("linked")


def test_irrelevant_photo_is_flagged_and_does_not_raise_confidence(fresh):
    r = submit(fresh, "clear_sky_park.png", DELHI)
    assert r["status"] == "rejected" and r["verification"]["is_pollution_event"] is False
    assert r["impact"]["cell_confidence_after"] == r["impact"]["cell_confidence_before"]
    assert r["impact"]["alert_id"] is None


def test_cross_boundary_punjab_to_delhi(fresh):
    c = fresh
    pb = c.get("/api/alerts?jurisdiction=PB-PPCB").json()[0]
    sug = pb["cross_boundary_suggestion"]
    assert sug and sug["target_jurisdiction_id"] == "DL-DPCC"
    c.post(f"/api/alerts/{pb['alert_id']}/acknowledge", json={"officer": "officer.pb"})
    xa = c.post(f"/api/alerts/{pb['alert_id']}/cross-boundary", json={"officer": "officer.pb"}).json()
    assert xa["kind"] == "cross_boundary" and xa["jurisdiction_id"] == "DL-DPCC"
    assert xa["origin_jurisdiction_id"] == "PB-PPCB" and xa["status"] == "pending_review"
    assert any(a["action_id"] == "DL-CROSS-BOUNDARY-LIAISON" for a in xa["action_brief"]["recommended_actions"])
    inbox = c.get("/api/alerts?jurisdiction=DL-DPCC").json()
    assert [a["alert_id"] for a in inbox] == [xa["alert_id"]]
    assert c.post(f"/api/alerts/{pb['alert_id']}/cross-boundary", json={"officer": "officer.pb"}).status_code == 409
    analytics = c.get("/api/cities/delhi-ncr/analytics").json()
    assert analytics["cross_boundary_in"] == 1


def test_forecast_and_multilingual_advisory_need_approval(fresh):
    c = fresh
    fc = c.get("/api/cities/delhi-ncr/forecast").json()
    assert [h["horizon_hours"] for h in fc["horizons"]] == [24, 48, 72]
    adv = c.post("/api/advisories/generate", json={"state": "punjab"}).json()
    assert adv["status"] == "draft"
    assert set(adv["translations"]) == {"en", "hi", "pa"}
    assert adv["translations"]["pa"]["headline"] != adv["translations"]["en"]["headline"]
    assert c.get("/api/advisories?state=punjab&status=approved").json() == []
    approved = c.post(f"/api/advisories/{adv['advisory_id']}/approve", json={"officer": "officer.pb"}).json()
    assert approved["status"] == "approved"
    assert len(c.get("/api/advisories?state=punjab&status=approved").json()) == 1
