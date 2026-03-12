from .agents import DataScientistAgent, AuditorAgent, BusinessReviewerAgent
from typing import Any, Dict, Optional


class MultiAgentSystem:
    """Coordinator that runs the three agents in sequence."""

    def __init__(self, kpis: Optional[Dict[str, Any]] = None):
        self.ds = DataScientistAgent()
        self.auditor = AuditorAgent()
        self.reviewer = BusinessReviewerAgent(kpis=kpis)

    def run_workflow(self, X, y, model_cls, **model_kwargs):
        if model_cls is None:
            raise ValueError("model_cls must be provided")
        results: Dict[str, Any] = {}
        # step 1: build model
        model = self.ds.build_model(X, y, model_cls, **model_kwargs)
        results["model"] = model
        # step 2: audit
        results["leakage"] = self.auditor.check_leakage(X, y)
        # note: bias check requires dataset with protected attribute
        # results['bias'] = self.auditor.check_bias(...)
        results["methodology"] = self.auditor.review_methodology("Auto run")
        # step 3: business review
        results["kpi_review"] = self.reviewer.assess_kpi_alignment(model, "default")
        results["meta"] = {
            "rows": int(len(X)) if hasattr(X, "__len__") else None,
            "features": (
                int(getattr(X, "shape", [0, 0])[1]) if hasattr(X, "shape") else None
            ),
        }
        return results
