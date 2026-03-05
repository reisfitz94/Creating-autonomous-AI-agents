from typing import Dict, Any

import numpy as np
from sklearn.linear_model import LinearRegression


def run_experiment(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run a toy experiment and return a result summary.

    Currently this function generates a random regression problem using the
    hyperparameters passed in ``params`` (e.g. ``features`` size, ``samples``
    count) and fits a ``LinearRegression`` model.  The returned dictionary
    contains the model's coefficient of determination (R^2) as the ``score``.

    ``params`` may be extended in the future to point at real training data
    or to dispatch to an external experiment tracking service.
    """
    features = params.get("features", 3)
    samples = params.get("samples", 100)
    rng = np.random.default_rng()
    X = rng.standard_normal((samples, features))
    y = rng.standard_normal(samples)

    model = LinearRegression().fit(X, y)
    r2 = model.score(X, y)

    result = {"name": name, "params": params, "score": r2}

    # optionally log to MLflow if available and configured
    try:
        import os
        import mlflow

        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI")
        if mlflow_uri:
            mlflow.set_tracking_uri(mlflow_uri)
            with mlflow.start_run(run_name=name):
                mlflow.log_params(params)
                mlflow.log_metric("r2", r2)
    except ImportError:
        # mlflow not installed; ignore silently
        pass
    except Exception as e:
        # logging failure should not break the experiment
        print(f"MLflow logging failed: {e}")

    return result
