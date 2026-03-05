from ai_safety_agent.agent import SafetyAgent


def test_offenders_within_radius():
    # create dummy registry entries
    registry = [
        {"latitude": 40.0, "longitude": -75.0, "name": "A"},
        {"latitude": 41.0, "longitude": -75.0, "name": "B"},
    ]
    agent = SafetyAgent(registry_data=registry)
    center = {"latitude": 40.0, "longitude": -75.0}
    results = agent.offenders_within_radius(center, radius_miles=70)
    assert len(results) >= 1
    assert results[0]["name"] == "A"


def test_geocode_service(monkeypatch):
    agent = SafetyAgent(
        registry_data=[{"latitude": 40.0, "longitude": -75.0, "name": "Offender"}]
    )

    class FakeLocation:
        latitude = 40.0
        longitude = -75.0

    class FakeGeo:
        def __init__(self, user_agent=None):
            pass

        def geocode(self, address, timeout=None):
            return FakeLocation()

    # patch the geopy class used inside the method
    import geopy.geocoders

    monkeypatch.setattr(geopy.geocoders, "Nominatim", FakeGeo)
    center = agent.geocode("123 Main St")
    assert center["latitude"] == 40.0
    result = agent.query_address("123 Main St")
    assert result and result[0]["name"] == "Offender"
