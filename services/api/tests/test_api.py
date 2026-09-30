def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200 and res.json()["status"] == "ok"


def test_config_reports_demo_mode(client):
    body = client.get("/api/config").json()
    assert body["demo_mode"] is True
    assert {i["name"] for i in body["integrations"]} >= {"gemini", "earth_engine", "cpcb", "text_to_speech"}


def test_cities_and_models(client):
    cities = client.get("/api/cities").json()
    assert len(cities) >= 2
    models = client.get("/api/models").json()
    shared = next(m for m in models if m["id"] == "igp-smog-forecast-v1")
    assert set(shared["used_by"]) >= {"delhi-ncr", "punjab"}
    card = client.get("/api/models/igp-smog-forecast-v1/card").json()
    assert "metrics_mae_vs_persistence" in card["card"]
    assert client.get("/api/models/nope/card").status_code == 404


def test_grid_and_canonical_cell(fresh):
    grid = fresh.get("/api/grid?city=delhi-ncr").json()
    assert len(grid["cells"]) == 37 and grid["is_sample_data"] is True
    assert {f["signal"] for f in grid["freshness"]} >= {"Satellite NO2", "Fire detections", "Official station"}
    top = max(grid["cells"], key=lambda c: c["confidence"])
    cell = fresh.get(f"/api/cells/{top['h3_cell']}").json()
    for key in ("state", "city", "cell_id", "timestamp", "observations", "weather", "citizen_reports", "hotspot",
                "forecast"):
        assert key in cell
    assert set(cell["forecast"]) == {"pm25_24h", "pm25_48h", "pm25_72h"}
    assert len(cell["confidence_breakdown"]["factors"]) == 4
    fc = fresh.get(f"/api/cells/{top['h3_cell']}/forecast").json()
    assert len(fc["horizons"]) == 3
    assert fresh.get("/api/grid?city=atlantis").status_code == 404
    assert fresh.get("/api/cells/not-a-cell").status_code == 404


def test_sensors_list_and_ingest(fresh):
    sensors = fresh.get("/api/sensors?city=punjab").json()
    assert sensors["official_station"]["type"] == "official"
    sid = sensors["low_cost"][0]["sensor_id"]
    body = {"timestamp": "2026-09-30T10:00:00+05:30", "pm25_raw": 300, "pm10": 420, "temperature": 20,
            "humidity": 80}
    assert fresh.post(f"/api/sensors/{sid}/observations", json=body).status_code == 401
    res = fresh.post(f"/api/sensors/{sid}/observations", json=body, headers={"X-Ingest-Token": "test-token"})
    assert res.status_code == 200
    obs = res.json()
    assert obs["pm25_calibrated"] < obs["pm25_raw"] and obs["indicative"] and obs["is_simulated"] is False
    assert fresh.post("/api/sensors/NOPE/observations", json=body,
                      headers={"X-Ingest-Token": "test-token"}).status_code == 404


def test_seeded_hotspots_and_regenerate_brief(fresh):
    hs = fresh.get("/api/hotspots?city=punjab").json()
    assert hs and hs[0]["likely_sources"][0]["type"] == "crop_residue_burning"
    detail = fresh.get(f"/api/hotspots/{hs[0]['hotspot_id']}").json()
    assert detail["evidence_bundle"]["citizen_reports"]
    assert detail["alert"]["status"] == "pending_review"
    regen = fresh.post(f"/api/hotspots/{hs[0]['hotspot_id']}/brief").json()
    assert regen["brief"]["requires_human_review"] is True
    assert fresh.get("/api/hotspots/HS-nope").status_code == 404


def test_alert_state_machine_guards(fresh):
    alert = fresh.get("/api/alerts?jurisdiction=MH-MPCB").json()[0]
    aid = alert["alert_id"]
    assert fresh.post(f"/api/alerts/{aid}/close", json={"officer": "o", "resolution": "x"}).status_code == 409
    assert fresh.post(f"/api/alerts/{aid}/action", json={"officer": "o", "action_taken": "x"}).status_code == 409
    assert fresh.post(f"/api/alerts/{aid}/cross-boundary", json={"officer": "o"}).status_code == 409
    assert fresh.post("/api/alerts/nope/acknowledge", json={"officer": "o"}).status_code == 404


def test_translate_and_tts_demo(client):
    t = client.post("/api/translate", json={"texts": ["hello"], "target": "hi"}).json()
    assert t["mode"] == "demo"
    s = client.post("/api/text-to-speech", json={"text": "नमस्ते", "language": "hi"}).json()
    assert s["mode"] == "demo" and s["engine"] == "browser_speech_synthesis" and s["locale"] == "hi-IN"


def test_report_outside_pilot_area(fresh):
    from app.config import settings

    photo = (settings.sample_data_dir / "photos" / "industrial_chimney_smoke.jpg").read_bytes()
    r = fresh.post("/api/reports", files={"photo": ("p.jpg", photo, "image/jpeg")},
                   data={"lat": "12.97", "lon": "77.59"}).json()
    assert r["status"] == "outside_pilot_area"
    assert fresh.get(f"/api/reports/{r['report_id']}").status_code == 200
    assert fresh.get("/api/reports/RP-nope").status_code == 404


def test_locate_and_sample_photos(client):
    loc = client.get("/api/locate?lat=28.628&lon=77.295").json()
    assert loc["state"] == "delhi-ncr" and loc["in_demo_grid"] and loc["jurisdiction"]["id"] == "DL-DPCC"
    assert client.get("/api/locate?lat=12.97&lon=77.59").json()["in_pilot_area"] is False
    photos = client.get("/api/samples/photos").json()
    assert len(photos) == 4
    assert client.get(photos[0]["url"]).status_code == 200
    assert client.get("/api/samples/photos/..%2F..%2Fsecret").status_code == 404


def test_voice_and_location_fall_back_in_demo_mode(client):
    stt = client.post("/api/speech-to-text", files={"audio": ("n.webm", b"\x1a\x45\xdf\xa3" * 64, "audio/webm")},
                      data={"language": "hi"}).json()
    assert stt["mode"] == "demo" and stt["transcript"] == ""
    geo = client.get("/api/geocode?q=Patparganj").json()
    assert geo["mode"] == "demo" and geo["results"] == []
    assert client.get("/api/geocode/reverse?lat=28.6&lon=77.3").json() == {"mode": "demo", "result": None}
    names = {i["name"] for i in client.get("/api/config").json()["integrations"]}
    assert {"speech_to_text", "maps"} <= names


def test_sample_photos_carry_attribution(client):
    photos = client.get("/api/samples/photos").json()
    assert len(photos) == 4
    assert all("Wikimedia Commons" in p["attribution"] and p["source_url"] for p in photos)
    assert client.get(photos[0]["url"]).headers["content-type"] == "image/jpeg"
