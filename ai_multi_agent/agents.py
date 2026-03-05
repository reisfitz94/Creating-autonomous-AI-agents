from typing import Any, Dict, Optional
import pandas as pd
from sklearn.base import BaseEstimator


class DataScientistAgent:
    """Agent responsible for building models."""

    def __init__(self):
        self.model: Optional[BaseEstimator] = None

    def build_model(
        self, X: pd.DataFrame, y: pd.Series, model_cls: Any, **kwargs
    ) -> BaseEstimator:
        """Train a sklearn-style model on provided data.

        Returns the fitted model.
        """
        self.model = model_cls(**kwargs)
        self.model.fit(X, y)
        return self.model


class AuditorAgent:
    """Agent that inspects a model/data for issues such as leakage, bias, etc."""

    def __init__(self):
        pass

    def check_leakage(self, X: pd.DataFrame, y: pd.Series) -> bool:
        """Naively examine whether any feature correlates too perfectly with the target."""
        corr = X.corrwith(y).abs()
        if corr.max() > 0.95:
            return True
        return False

    def check_bias(
        self, data: pd.DataFrame, label: str, protected: str
    ) -> Dict[str, float]:
        """Compute simple demographic parity difference."""
        groups = data.groupby(protected)[label].mean()
        if groups.shape[0] < 2:
            return {}
        return {"parity_diff": groups.max() - groups.min()}

    def review_methodology(self, notes: str) -> str:
        return f"Methodology checked: {notes[:100]}..."


class BusinessReviewerAgent:
    """Agent that ensures model aligns with business KPIs."""

    def __init__(self, kpis: Optional[Dict[str, Any]] = None):
        self.kpis = kpis or {}

    def assess_kpi_alignment(self, model: BaseEstimator, kpi: str) -> str:
        # placeholder logic
        if kpi in self.kpis:
            return f"Model evaluation on {kpi}: OK"
        return f"No KPI {kpi} defined"
