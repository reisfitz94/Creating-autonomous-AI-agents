from fastapi import FastAPI
from .orchestrator import MarketOpsCommander

app = FastAPI()
commander = MarketOpsCommander()


@app.get("/status")
def status():
    return {"logs": commander.memory.get("logs", [])}


@app.post("/run")
def run():
    ops = commander.run_loop()
    return {"opportunities": ops}


@app.get("/strategy")
def get_strategy():
    return {"strategy": commander.memory.get("strategy", {})}


@app.post("/experiment")
def start_experiment(name: str, features: int = 3, samples: int = 100):
    from .experiments.run import run_experiment

    res = run_experiment(name, {"features": features, "samples": samples})
    return res
