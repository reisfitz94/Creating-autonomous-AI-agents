from typing import Any, Dict


class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> Any:
        raise NotImplementedError


class ExecutiveAgent(BaseAgent):
    def __init__(self):
        super().__init__("Executive")

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> str:
        return f"Executive sets objectives: {task.get('objective', '')}"


class TechnicalLeadAgent(BaseAgent):
    def __init__(self):
        super().__init__("TechnicalLead")

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> str:
        return "Technical lead defines architecture"


class DataScientistAgent(BaseAgent):
    def __init__(self):
        super().__init__("DataScientist")

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> str:
        return "Data scientist builds prototype model"


class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Auditor")

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> str:
        return "Auditor checks for leakage and bias"


class RiskComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__("RiskCompliance")

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> str:
        return "Risk agent reviews regulatory compliance"


class DeploymentEngineerAgent(BaseAgent):
    def __init__(self):
        super().__init__("DeploymentEngineer")

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> str:
        return "Deployment engineer packages artifacts"


class MonitoringAgent(BaseAgent):
    def __init__(self):
        super().__init__("Monitoring")

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> str:
        return "Monitoring agent watches performance and drift"

    def detect_drift(self, data: list) -> bool:
        # simple change detection: check if mean shifts by >10%
        if not data:
            return False
        mean = sum(data) / len(data)
        start = sum(data[: max(1, len(data) // 4)]) / max(1, len(data) // 4)
        return abs(mean - start) / (start + 1e-9) > 0.1


class CostOptimizationAgent(BaseAgent):
    def __init__(self):
        super().__init__("CostOptimization")

    def act(self, task: Dict[str, Any], memory: Dict[str, Any]) -> str:
        return "Cost agent estimates compute/token expense"
