import schedule
import time
from .orchestrator import MarketOpsCommander


def run_periodic(
    interval_minutes: int = 60,
    interval_seconds: float | None = None,
    max_cycles: int | None = None,
):
    moc = MarketOpsCommander()
    if interval_seconds is not None:
        schedule.every(interval_seconds).seconds.do(moc.run_loop)
    else:
        schedule.every(interval_minutes).minutes.do(moc.run_loop)
    cycles = 0
    while True:
        schedule.run_pending()
        time.sleep(1)
        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            break
