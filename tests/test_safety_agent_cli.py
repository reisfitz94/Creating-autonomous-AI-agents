import sys
from ai_safety_agent import cli


def test_safety_cli(monkeypatch, capsys):
    # monkeypatch geocode to return a fixed point
    monkeypatch.setattr(
        cli.SafetyAgent,
        "geocode",
        lambda self, addr: {"latitude": 40, "longitude": -75},
    )

    # simulate CLI invocation
    monkeypatch.setattr(sys, "argv", ["ai_safety_agent", "123 Main St"])
    cli.main()
    captured = capsys.readouterr()
    assert "Example Offender" in captured.out
