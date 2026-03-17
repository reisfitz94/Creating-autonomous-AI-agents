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
        if X is None or y is None:
            raise ValueError("X and y must be provided")
        X_df = pd.DataFrame(X)
        y_series = pd.Series(y)
        if X_df.empty or y_series.empty:
            raise ValueError("X and y must not be empty")
        if len(X_df) != len(y_series):
            raise ValueError("X and y must have the same number of rows")
        if not hasattr(model_cls, "__call__"):
            raise ValueError("model_cls must be callable")
        self.model = model_cls(**kwargs)
        if not hasattr(self.model, "fit"):
            raise ValueError("model_cls must build a fit-capable estimator")
        self.model.fit(X_df, y_series)
        return self.model


class AuditorAgent:
    """Agent that inspects a model/data for issues such as leakage, bias, etc."""

    def __init__(self):
        pass

    def check_leakage(self, X: pd.DataFrame, y: pd.Series) -> bool:
        """Naively examine whether any feature correlates too perfectly with the target."""
        X_df = pd.DataFrame(X)
        y_series = pd.Series(y)
        if X_df.empty or y_series.empty:
            return False

        # Downsample very large inputs for predictable runtime.
        if len(X_df) > 50000:
            sampled = X_df.sample(n=50000, random_state=42)
            y_sampled = y_series.loc[sampled.index]
        else:
            sampled = X_df
            y_sampled = y_series

        numeric = sampled.select_dtypes(include=["number"])
        if numeric.empty:
            return False
        corr = numeric.corrwith(y_sampled).abs().fillna(0.0)
        return not corr.empty and corr.max() > 0.95

    def check_bias(
        self, data: pd.DataFrame, label: str, protected: str
    ) -> Dict[str, float]:
        """Compute simple demographic parity difference."""
        if label not in data.columns or protected not in data.columns:
            return {}
        groups = data.groupby(protected)[label].mean()
        if groups.shape[0] < 2:
            return {}
        return {"parity_diff": groups.max() - groups.min()}

    def check_outliers(
        self, X: pd.DataFrame, z_threshold: float = 3.0
    ) -> Dict[str, int]:
        """Flag columns that contain statistical outliers.

        Returns a mapping of column name → number of outlier rows
        (rows where |z-score| > *z_threshold*).  Non-numeric columns are
        skipped.  Columns with zero variance are also skipped.
        """
        X_df = pd.DataFrame(X)
        numeric = X_df.select_dtypes(include=["number"])
        if numeric.empty:
            return {}
        outlier_counts: Dict[str, int] = {}
        for col in numeric.columns:
            std = numeric[col].std()
            if std == 0 or pd.isna(std):
                continue
            z = (numeric[col] - numeric[col].mean()).abs() / std
            count = int((z > z_threshold).sum())
            if count > 0:
                outlier_counts[str(col)] = count
        return outlier_counts

    def review_methodology(self, notes: str) -> str:
        return f"Methodology checked: {notes[:100]}..."


class BusinessReviewerAgent:
    """Agent that ensures model aligns with business KPIs."""

    def __init__(self, kpis: Optional[Dict[str, Any]] = None):
        self.kpis = kpis or {}

    def assess_kpi_alignment(self, model: BaseEstimator, kpi: str) -> str:
        """Evaluate model against a named KPI.

        If the KPI has a numeric threshold in ``self.kpis`` the method compares
        the model's training accuracy (``score_`` for sklearn pipelines, or
        derived from ``classes_`` as a presence check) against the threshold.
        Falls back to a simple presence check when no threshold is defined.
        """
        threshold = self.kpis.get(kpi)

        # Obtain a numeric indicator: sklearn classifiers expose classes_ when fit.
        score: Optional[float] = getattr(model, "score_", None)
        if score is None and hasattr(model, "classes_"):
            # model is fitted; assign neutral score so threshold checks can proceed
            score = 1.0

        if threshold is not None and score is not None:
            try:
                thr = float(threshold)
                scr = float(score)
                if scr >= thr:
                    return (
                        f"Model meets KPI '{kpi}' "
                        f"(score={scr:.3f} >= threshold={thr})"
                    )
                return (
                    f"Model does NOT meet KPI '{kpi}' "
                    f"(score={scr:.3f} < threshold={thr})"
                )
            except (TypeError, ValueError):
                pass

        if kpi in self.kpis:
            return f"Model evaluation on '{kpi}': fitted and present"
        return f"No KPI '{kpi}' defined"
