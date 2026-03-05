import argparse
from .agent import SafetyAgent


def main():
    parser = argparse.ArgumentParser(description="Safety agent CLI")
    parser.add_argument("address", help="Address to check")
    parser.add_argument("--radius", type=float, default=50.0, help="Radius in miles")
    args = parser.parse_args()

    # sample registry data; real application would query a database or API
    registry = [{"latitude": 40.0, "longitude": -75.0, "name": "Example Offender"}]
    agent = SafetyAgent(registry_data=registry)
    try:
        center = agent.geocode(args.address)
    except Exception as e:
        print(f"Geocoding failed: {e}")
        return
    offenders = agent.offenders_within_radius(center, args.radius)
    if not offenders:
        print("No offenders found within radius.")
    else:
        for o in offenders:
            print(f"{o.get('name')} at {o.get('distance_miles'):.1f} miles")


if __name__ == "__main__":
    main()
