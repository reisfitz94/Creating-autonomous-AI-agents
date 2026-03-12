from typing import List, Dict, Any, Optional
from geopy.distance import geodesic
import math


class SafetyAgent:
    """Agent to check for registered offenders near an address.

    **Disclaimer**: this is a conceptual example. Actual systems must conform to
    all applicable laws, use trusted public-source data, and protect privacy.
    """

    def __init__(self, registry_data: Optional[List[Dict[str, Any]]] = None):
        # registry_data is expected to be a list of dicts with fields
        # 'latitude', 'longitude', and any other metadata.
        self.registry = registry_data or []
        self._geocode_cache: Dict[str, Dict[str, float]] = {}

    def geocode(self, address: str) -> Dict[str, float]:
        """Resolve an address to latitude/longitude using Nominatim.

        Falls back to raising ``ValueError`` if the lookup fails.  This requires
        network access and the `geopy` package (already installed).  In real
        deployments one might use a paid geocoding service with an API key or a
        local database.
        """
        normalized = (address or "").strip().lower()
        if not normalized:
            raise ValueError("address cannot be empty")
        if normalized in self._geocode_cache:
            return self._geocode_cache[normalized]

        try:
            from geopy.geocoders import Nominatim

            geolocator = Nominatim(user_agent="safety_agent")
            loc = geolocator.geocode(normalized, timeout=10)
            if not loc:
                raise ValueError(f"could not geocode '{normalized}'")
            result = {"latitude": loc.latitude, "longitude": loc.longitude}
            self._geocode_cache[normalized] = result
            return result
        except Exception as e:
            raise ValueError(f"geocoding failed: {e}")

    def offenders_within_radius(
        self, center: Dict[str, float], radius_miles: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Return registry entries within `radius_miles` of the center point."""
        if radius_miles <= 0:
            return []

        center_lat = float(center["latitude"])
        center_lon = float(center["longitude"])
        lat_delta = radius_miles / 69.0
        lon_delta = radius_miles / max(1.0, 69.0 * math.cos(math.radians(center_lat)))

        result = []
        for entry in self.registry:
            lat = entry.get("latitude")
            lon = entry.get("longitude")
            if lat is None or lon is None:
                continue

            # Cheap bounding-box filter avoids expensive geodesic calls at scale.
            if abs(lat - center_lat) > lat_delta or abs(lon - center_lon) > lon_delta:
                continue

            try:
                dist = geodesic(
                    (center_lat, center_lon),
                    (lat, lon),
                ).miles
            except Exception:
                continue
            if dist <= radius_miles:
                e = entry.copy()
                e["distance_miles"] = dist
                result.append(e)
        result.sort(key=lambda x: x["distance_miles"])
        return result

    def query_address(
        self, address: str, radius_miles: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Top-level method that geocodes an address and searches the registry."""
        center = self.geocode(address)
        return self.offenders_within_radius(center, radius_miles)
