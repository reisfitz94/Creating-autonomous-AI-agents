import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Optional


class AIProjectManagerAgent:
    """An autonomous agent for technical project management tasks.

    Capabilities:
      - Convert Jira tickets into dependency graphs
      - Identify bottlenecks
      - Predict sprint slippage
      - Summarize risk exposure
      - Suggest mitigation plans
      - (Optional) Integrate with GitHub commit velocity
      - (Optional) Burn-down anomaly detection
    """

    def __init__(self, jira_client=None, github_client=None):
        # jira_client and github_client are expected to be client objects from

        # their respective APIs (e.g. `jira` Python library and `PyGithub`).
        self.jira = jira_client
        self.github = github_client

    def fetch_jira_tickets(self, jql: str) -> List[Dict[str, Any]]:
        """Fetch tickets from Jira using a JQL query.

        Returns a list of issue dictionaries as returned by the Jira API.
        """
        if not self.jira:
            raise RuntimeError("Jira client has not been configured")
        if not jql or not str(jql).strip():
            raise ValueError("jql query cannot be empty")
        issues = self.jira.search_issues(jql)
        return [issue.raw for issue in issues]

    def build_dependency_graph(self, tickets: List[Dict[str, Any]]) -> nx.DiGraph:
        """Construct a directed graph where nodes are tickets and edges represent
        'blocks' or 'depends on' relationships.
        """
        G = nx.DiGraph()
        for ticket in tickets:
            key = ticket.get("key")
            if not key:
                continue
            G.add_node(key, **ticket)
            # Example: look for "issuelinks" with "blocks" or "depends on"
            for link in ticket.get("fields", {}).get("issuelinks", []):
                if link.get("type", {}).get("name") in (
                    "Blocks",
                    "Depends",
                ):  # adjust as needed
                    outward = link.get("outwardIssue")
                    inward = link.get("inwardIssue")
                    if outward:
                        G.add_edge(key, outward.get("key"))
                    if inward:
                        G.add_edge(inward.get("key"), key)
        return G

    def identify_bottlenecks(self, graph: nx.DiGraph, top_n: int = 5) -> List[str]:
        """Identify bottleneck tickets using centrality metrics.

        Returns the keys of the top_n nodes by betweenness centrality.
        """
        if graph.number_of_nodes() == 0:
            return []

        # Exact betweenness is expensive for very large graphs.
        if graph.number_of_nodes() > 1000:
            centrality = nx.degree_centrality(graph)
        else:
            centrality = nx.betweenness_centrality(graph)
        sorted_nodes = sorted(centrality.items(), key=lambda x: -x[1])
        limit = max(1, int(top_n))
        return [node for node, _ in sorted_nodes[:limit]]

    def predict_sprint_slippage(
        self,
        velocity_history: List[int],
        remaining_work: int,
        model: Optional[Any] = None,
    ) -> float:
        """Predict sprint slippage based on past velocity and remaining work.

        A very simple heuristic: average velocity vs remaining work. Advanced users
        can supply a statistical/regression model as `model`.
        """
        if model is not None:
            return model.predict(
                pd.DataFrame(
                    {"velocity": velocity_history, "remaining": [remaining_work]}
                )
            )[0]
        if not velocity_history:
            return float("inf")
        avg_velocity = sum(velocity_history) / len(velocity_history)
        if avg_velocity <= 0:
            return float("inf")
        return remaining_work / avg_velocity

    def summarize_risk_exposure(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Walk through tickets looking for risk markers and aggregate them.

        This implementation assumes a custom field or label called 'risk'.
        """
        risk_summary: Dict[str, int] = {}
        for ticket in tickets:
            labels = ticket.get("fields", {}).get("labels", [])
            for label in labels:
                if label.startswith("risk:"):
                    risk_summary[label] = risk_summary.get(label, 0) + 1
        return {
            "total_tickets": len(tickets),
            "risk_count": sum(risk_summary.values()),
            "by_label": risk_summary,
        }

    def suggest_mitigation_plans(self, risk_summary: Dict[str, Any]) -> List[str]:
        """Generate simple mitigation suggestions from a risk summary.

        The current heuristic produces more urgent language when a particular
        label appears frequently; production systems could instead link to
        documented procedures, trigger automated workflows, or involve
        stakeholders.  Removing this comment now that the method implements a
        basic policy that can be extended.
        """
        plans: List[str] = []
        for label, count in risk_summary.get("by_label", {}).items():
            if count > 10:
                plans.append(f"Immediate action required for {label}: {count} tickets")
            elif count > 5:
                plans.append(f"Investigate {label} risks: {count} tickets")
            else:
                plans.append(f"Monitor {label} risks ({count})")
        return plans

    # Optional helpers
    def compute_commit_velocity(self, repo_name: str, days: int = 14) -> float:
        """Calculate average commits per day for a GitHub repository."""
        if not self.github:
            raise RuntimeError("GitHub client not configured")
        if days <= 0:
            raise ValueError("days must be > 0")
        repo = self.github.get_repo(repo_name)
        commits = repo.get_commits(since=pd.Timestamp.now() - pd.Timedelta(days=days))
        return commits.totalCount / days

    def detect_burndown_anomalies(self, burndown_data: pd.DataFrame) -> List[int]:
        """Detect days where the burndown deviated significantly from trend."""
        # simple z-score on daily remaining work
        if "remaining" not in burndown_data.columns or burndown_data.empty:
            return []
        burndown_data = burndown_data.copy()
        std = burndown_data["remaining"].std()
        if std == 0 or pd.isna(std):
            return []
        burndown_data["z"] = (
            burndown_data["remaining"] - burndown_data["remaining"].mean()
        ) / std
        return burndown_data[burndown_data["z"].abs() > 2].index.tolist()
