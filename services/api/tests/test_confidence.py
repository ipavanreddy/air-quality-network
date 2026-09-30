import pytest

from app.hotspots import confidence as hc


def test_weights_match_prd():
    assert hc.WEIGHTS == {"sensor_anomaly": 0.35, "satellite": 0.25, "citizen_reports": 0.25, "weather": 0.15}
    assert sum(hc.WEIGHTS.values()) == pytest.approx(1.0)


def test_sensor_anomaly_scales_with_ratio():
    assert hc.sensor_anomaly(100, 100).score == 0
    assert hc.sensor_anomaly(150, 100).score == pytest.approx(50)
    assert hc.sensor_anomaly(400, 100).score == 100
    # PM10 ratio can dominate (construction dust)
    assert hc.sensor_anomaly(100, 100, 300, 100).score == 100
    missing = hc.sensor_anomaly(None, 100)
    assert missing.score == 0 and not missing.available


def test_satellite_takes_strongest_signal():
    f = hc.satellite(no2_anomaly_pct=30, fire_count_upwind=40, aod=0.5)
    assert f.score == 100  # fires saturate
    assert hc.satellite(42, 0, 0.4).score == pytest.approx(70)
    assert not hc.satellite(None, None, None).available


def test_citizen_reports_combine_and_decay_with_distance():
    one = hc.citizen_reports([(0.9, 5, 0)]).score
    two = hc.citizen_reports([(0.9, 5, 0), (0.9, 5, 0)]).score
    far = hc.citizen_reports([(0.9, 5, 1)]).score
    assert one == pytest.approx(90)
    assert two > one and two <= 100
    assert far < one
    assert hc.citizen_reports([]).score == 0


def test_weather_stagnation_and_plausibility():
    calm = hc.weather(1.0, 200, True).score
    windy = hc.weather(6.0, 1500, True).score
    implausible = hc.weather(1.0, 200, False).score
    assert calm == pytest.approx(100)
    assert windy == pytest.approx(50)
    assert implausible < calm
    assert hc.weather(1.0, None, True).score == pytest.approx(100)


def test_combine_breakdown_and_bands():
    factors = [hc.sensor_anomaly(290, 112), hc.satellite(42, 0, 1.2), hc.citizen_reports([(0.86, 4, 0)]),
               hc.weather(1.1, 220, True)]
    out = hc.combine(factors)
    assert out["confidence"] == pytest.approx(sum(f["contribution"] for f in out["factors"]), abs=0.3)
    assert out["band"] == "High" and out["confidence"] >= 75
    assert out["evidence_types"] == 4
    assert {f["name"] for f in out["factors"]} == set(hc.WEIGHTS)
    assert hc.band(60) == "Medium" and hc.band(10) == "Low"


def test_angle_helpers():
    assert hc.angle_diff(350, 10) == 20
    assert 80 < hc.bearing_deg(28.6, 77.2, 28.6, 77.3) < 100  # east
