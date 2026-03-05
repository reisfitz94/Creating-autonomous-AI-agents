from typing import List, Dict, Any
from geopy.distance import geodesic


class SafetyAgent:
    """Agent to check for registered offenders near an address.

    **Disclaimer**: this is a conceptual example. Actual systems must conform to
    all applicable laws, use trusted public-source data, and protect privacy.
    """

    def __init__(self, registry_data: List[Dict[str, Any]] = None):
        # registry_data is expected to be a list of dicts with fields
        # 'latitude', 'longitude', and any other metadata.
        self.registry = registry_data or []

    def geocode(self, address: str) -> Dict[str, float]:
        """Resolve an address to latitude/longitude using Nominatim.

        Falls back to raising ``ValueError`` if the lookup fails.  This requires
        network access and the `geopy` package (already installed).  In real
        deployments one might use a paid geocoding service with an API key or a
        local database.
        """
        try:
            from geopy.geocoders import Nominatim

            geolocator = Nominatim(user_agent="safety_agent")
            loc = geolocator.geocode(address, timeout=10)
            if not loc:
                raise ValueError(f"could not geocode '{address}'")
            return {"latitude": loc.latitude, "longitude": loc.longitude}
        except Exception as e:
            raise ValueError(f"geocoding failed: {e}")

    def offenders_within_radius(
        self, center: Dict[str, float], radius_miles: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Return registry entries within `radius_miles` of the center point."""
        result = []
        for entry in self.registry:
            try:
                dist = geodesic(
                    (center["latitude"], center["longitude"]),
                    (entry["latitude"], entry["longitude"]),
                ).miles
            except Exception:
                continue
            if dist <= radius_miles:
                e = entry.copy()
                e["distance_miles"] = dist
                result.append(e)
        return result

    def query_address(
        self, address: str, radius_miles: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Top-level method that geocodes an address and searches the registry."""
        center = self.geocode(address)
        return self.offenders_within_radius(center, radius_miles)
