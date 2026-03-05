"""Example entrypoint for the AI Technical Project Manager Agent."""

from ai_tpm_agent.agent import AIProjectManagerAgent


def main():
    # instantiate with real clients if available, else leave None for stubs
    agent = AIProjectManagerAgent(jira_client=None, github_client=None)

    # pretend we pulled some tickets already
    tickets = [
        {"key": "PROJ-1", "fields": {"labels": ["risk:high"], "issuelinks": []}},
        {"key": "PROJ-2", "fields": {"labels": [], "issuelinks": []}},
    ]

    graph = agent.build_dependency_graph(tickets)
    print("Dependency nodes:", graph.nodes())
    print("Bottlenecks:", agent.identify_bottlenecks(graph))
    print("Risk summary:", agent.summarize_risk_exposure(tickets))


if __name__ == "__main__":
    main()
