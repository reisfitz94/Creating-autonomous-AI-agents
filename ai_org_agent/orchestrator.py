from typing import Dict, Any, Optional
import random
from .agents import (
    ExecutiveAgent,
    TechnicalLeadAgent,
    DataScientistAgent,
    AuditorAgent,
    RiskComplianceAgent,
    DeploymentEngineerAgent,
    MonitoringAgent,
    CostOptimizationAgent,
)


class Orchestrator:
    """Meta-agent coordinating the organization with memory, tools, and critique."""

    def __init__(self, max_logs: int = 5000):
        from .vector_store import VectorStore

        self.memory: Dict[str, Any] = {"logs": []}
        self.vector_store = VectorStore()
        self.max_logs = max(100, int(max_logs))
        self.executive = ExecutiveAgent()
        self.tech_lead = TechnicalLeadAgent()
        self.ds = DataScientistAgent()
        self.auditor = AuditorAgent()
        self.risk = RiskComplianceAgent()
        self.deploy = DeploymentEngineerAgent()
        self.monitor = MonitoringAgent()
        self.cost = CostOptimizationAgent()

    def log(self, message: str):
        msg = str(message)
        print(f"[LOG] {msg}")
        self.memory["logs"].append(msg)
        if len(self.memory["logs"]) > self.max_logs:
            self.memory["logs"] = self.memory["logs"][-self.max_logs :]

    def store_vector(self, item: Dict[str, Any]):
        # delegate to the vector store object
        safe_item = item or {}
        self.vector_store.add(str(safe_item.get("text", "")), metadata=safe_item)

    def retrieve_similar(self, query: str) -> Optional[Dict[str, Any]]:
        # proxy to vector store search
        return self.vector_store.search(query)

    def execute_tool(self, code: str) -> Any:
        """Safely evaluate a simple arithmetic expression.

        For security we parse with ``ast`` and ban names, calls, imports, and
        attribute access. Only numeric literals and operators are allowed.
        """
        import ast

        allowed_nodes = {
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Mod,
            ast.Pow,
            ast.FloorDiv,
            ast.USub,
            ast.UAdd,
            ast.Load,
            ast.Constant,
        }

        def _check(node: ast.AST):
            if isinstance(node, ast.Name):
                raise ValueError("names not allowed in tool code")
            if isinstance(node, ast.Call):
                raise ValueError("function calls are not permitted")
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute)):
                raise ValueError("imports/attributes not permitted")
            if type(node) not in allowed_nodes:
                raise ValueError(f"node type not allowed: {type(node).__name__}")
            for child in ast.iter_child_nodes(node):
                _check(child)

        try:
            tree = ast.parse(code, mode="eval")
            _check(tree)
            return eval(compile(tree, "<tool>", "eval"), {"__builtins__": {}}, {})
        except Exception as e:
            return f"tool_error: {e}"

    def self_critique(self, output: str, threshold: float = 0.5) -> bool:
        """Perform a naive self-critique of an output string.

        Currently the policy is very simple: if the text is empty, below a
        length threshold, or contains the word "error" the critique fails and
        a retry is triggered.  This can be replaced with more sophisticated NLP
        scoring or manual review.
        """
        if not output or len(output.strip()) < threshold * 100:
            return False
        if "error" in output.lower():
            return False
        return True

    def run_task(self, objective: str) -> Dict[str, Any]:
        objective = (objective or "").strip()
        if not objective:
            raise ValueError("objective cannot be empty")

        out = {}
        out["exec"] = self.executive.act({"objective": objective}, self.memory)
        self.log(out["exec"])
        self.store_vector({"text": out["exec"], "role": "exec"})

        out["arch"] = self.tech_lead.act({}, self.memory)
        self.log(out["arch"])
        self.store_vector({"text": out["arch"], "role": "tech"})

        out["model"] = self.ds.act({}, self.memory)
        self.log(out["model"])
        self.store_vector({"text": out["model"], "role": "ds"})

        # add critique step
        if not self.self_critique(out["model"]):
            self.log("Data scientist output failed critique, retrying")
            out["model"] = self.ds.act({}, self.memory)
            self.log(out["model"])

        out["audit"] = self.auditor.act({}, self.memory)
        self.log(out["audit"])
        self.store_vector({"text": out["audit"], "role": "audit"})
        out["risk"] = self.risk.act({}, self.memory)
        self.log(out["risk"])
        self.store_vector({"text": out["risk"], "role": "risk"})
        out["deploy"] = self.deploy.act({}, self.memory)
        self.log(out["deploy"])
        self.store_vector({"text": out["deploy"], "role": "deploy"})
        out["monitor"] = self.monitor.act({}, self.memory)
        self.log(out["monitor"])
        self.store_vector({"text": out["monitor"], "role": "monitor"})
        out["cost"] = self.cost.act({}, self.memory)
        self.log(out["cost"])
        self.store_vector({"text": out["cost"], "role": "cost"})
        return {"outputs": out, "memory": self.memory}

    def simulate_drift(self, data: list, noise_level: float = 0.5) -> list:
        """Produce a noisy version of the data to simulate drift or adversarial noise."""
        noisy = []
        for x in data:
            try:
                noisy.append(x + (noise_level * (0.5 - random.random())))
            except Exception:
                noisy.append(x)
        return noisy
