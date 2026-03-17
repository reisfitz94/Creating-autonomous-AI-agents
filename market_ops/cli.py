import argparse

from .orchestrator import MarketOpsCommander
from .scheduler import run_periodic


def main():
    parser = argparse.ArgumentParser(description="Market Ops Commander utilities")
    parser.add_argument("--db-path", help="path to sqlite file for persisting strategy")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("run", help="Execute one run of the orchestrator")
    sub.add_parser("status", help="Print current commander's logs and strategy")

    sched = sub.add_parser("schedule", help="Start periodic scheduler")
    sched.add_argument(
        "--interval", type=float, default=60, help="Minutes between runs"
    )

    api = sub.add_parser("api", help="Launch FastAPI server")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    if args.cmd == "run":
        moc = MarketOpsCommander(db_path=args.db_path)
        res = moc.run_loop()
        print(res)
    elif args.cmd == "status":
        moc = MarketOpsCommander(db_path=args.db_path)
        print(moc.memory)
    elif args.cmd == "schedule":
        run_periodic(interval_minutes=args.interval)
    elif args.cmd == "api":
        from uvicorn import run as uv_run

        uv_run("market_ops.api:app", host=args.host, port=args.port, reload=False)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
