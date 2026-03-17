from typing import Dict, Any, Optional, Callable
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
        self.max_logs = max(100, max_logs)
        self.executive = ExecutiveAgent()
        self.tech_lead = TechnicalLeadAgent()
        self.ds = DataScientistAgent()
        self.auditor = AuditorAgent()
        self.risk = RiskComplianceAgent()
        self.deploy = DeploymentEngineerAgent()
        self.monitor = MonitoringAgent()
        self.cost = CostOptimizationAgent()

    def log(self, message: str):
        print(f"[LOG] {message}")
        self.memory["logs"].append(message)
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
        """Safely evaluate a simple arithmetic expression using ast.literal_eval.

        SECURITY: Uses ast.literal_eval() instead of eval() to prevent remote code
        execution. Only numeric literals and basic operators are supported.
        """
        import ast
        import operator

        # Safe operator mapping for binary operations
        _BINARY_OPERATORS: Dict[type, Callable[[float, float], float]] = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
        }
        _UNARY_OPERATORS: Dict[type, Callable[[float], float]] = {
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def _evaluate(node: ast.expr) -> float:
            """Recursively evaluate AST nodes without using eval()."""
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError(f"unsupported constant: {node.value}")
            elif isinstance(node, ast.BinOp):
                left = _evaluate(node.left)
                right = _evaluate(node.right)
                op_binary = _BINARY_OPERATORS.get(type(node.op))
                if op_binary is None:
                    raise ValueError(f"unsupported operator: {type(node.op).__name__}")
                return op_binary(left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = _evaluate(node.operand)
                op_unary = _UNARY_OPERATORS.get(type(node.op))
                if op_unary is None:
                    raise ValueError(
                        f"unsupported unary operator: {type(node.op).__name__}"
                    )
                return op_unary(operand)
            else:
                raise ValueError(f"unsupported node type: {type(node).__name__}")

        try:
            tree = ast.parse(code, mode="eval")
            return _evaluate(tree.body)
        except (SyntaxError, ValueError, ZeroDivisionError) as e:
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
        return "error" not in output.lower()

    def run_task(self, objective: str) -> Dict[str, Any]:
        objective = (objective or "").strip()
        if not objective:
            raise ValueError("objective cannot be empty")

        out = {}
        out["exec"] = self.executive.act({"objective": objective}, self.memory)
        self.log(out["exec"])
        self.store_vector({"text": out["exec"], "role": "exec"})

        out["arch"] = self.tech_lead.act({"objective": objective}, self.memory)
        self.log(out["arch"])
        self.store_vector({"text": out["arch"], "role": "tech"})

        out["model"] = self.ds.act({"objective": objective}, self.memory)
        self.log(out["model"])
        self.store_vector({"text": out["model"], "role": "ds"})

        # add critique step
        if not self.self_critique(out["model"]):
            self.log("Data scientist output failed critique, retrying")
            out["model"] = self.ds.act({"objective": objective}, self.memory)
            self.log(out["model"])

        out["audit"] = self.auditor.act({"objective": objective}, self.memory)
        self.log(out["audit"])
        self.store_vector({"text": out["audit"], "role": "audit"})
        out["risk"] = self.risk.act({"objective": objective}, self.memory)
        self.log(out["risk"])
        self.store_vector({"text": out["risk"], "role": "risk"})
        out["deploy"] = self.deploy.act({"objective": objective}, self.memory)
        self.log(out["deploy"])
        self.store_vector({"text": out["deploy"], "role": "deploy"})
        out["monitor"] = self.monitor.act({"objective": objective}, self.memory)
        self.log(out["monitor"])
        self.store_vector({"text": out["monitor"], "role": "monitor"})
        out["cost"] = self.cost.act({"objective": objective}, self.memory)
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
