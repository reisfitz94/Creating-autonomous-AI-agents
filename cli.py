"""Simple CLI entrypoint for orchestrator."""

import argparse
from ai_org_agent.orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(description="Run the AI org orchestrator")
    parser.add_argument("objective", help="Business objective to pursue")
    parser.add_argument(
        "--simulate", action="store_true", help="Run a drift simulation example"
    )
    args = parser.parse_args()

    orch = Orchestrator()
    if args.simulate:
        print("Simulating drift on sample data:")
        data = [1, 2, 3, 4, 5]
        print("original", data)
        print("noisy", orch.simulate_drift(data))
        return

    result = orch.run_task(args.objective)
    print("Outputs:")
    for k, v in result["outputs"].items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
