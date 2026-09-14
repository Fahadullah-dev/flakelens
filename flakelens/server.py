import os

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from . import junit, runner
from .stats import classify

server = MCPServer("flakelens")


def _report(history):
    rows = []
    for test_id, (runs, failures) in sorted(history.items()):
        v = classify(runs, failures)
        rows.append({
            "test": test_id,
            "status": v.status,
            "runs": v.runs,
            "failures": v.failures,
            "failure_rate": round(v.failure_rate, 3),
            "confidence_interval": [round(v.ci_low, 3), round(v.ci_high, 3)],
        })
    return rows


@server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    )
)
def analyze_junit_history(directory: str) -> list[dict]:
    """Classifies tests as flaky, broken, stable, or unproven from past JUnit XML runs.

    Each .xml file in the directory is treated as one historical test run.
    """
    if not os.path.isdir(directory):
        raise ValueError(f"not a directory: {directory}")
    history = junit.load_history(directory)
    return _report(history)


@server.tool(
    annotations=ToolAnnotations(
        read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=True
    )
)
def run_flakiness_scan(test_path: str, runs: int = 20) -> list[dict]:
    """Runs a pytest suite repeatedly and classifies flaky tests from the results.

    Executes the target project's test code, which may touch the filesystem,
    network, or a database. Slower and more invasive than analyze_junit_history.
    """
    if not os.path.exists(test_path):
        raise ValueError(f"path does not exist: {test_path}")
    if runs < 5:
        raise ValueError("runs must be at least 5 for a meaningful confidence interval")
    history = runner.run_repeated(test_path, runs)
    return _report(history)


@server.tool(
    annotations=ToolAnnotations(
        read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
    )
)
def suggest_quarantine(directory: str, threshold: float = 0.1) -> dict:
    """Returns a pytest -m marker expression to skip tests flakier than the threshold."""
    if not os.path.isdir(directory):
        raise ValueError(f"not a directory: {directory}")
    history = junit.load_history(directory)
    flaky = [
        test_id for test_id, (runs, failures) in history.items()
        if classify(runs, failures).status == "flaky" and failures / runs >= threshold
    ]
    names = [t.split("::")[-1] for t in flaky]
    marker_expr = " and ".join(f"not {n}" for n in names) if names else ""
    return {"quarantine": sorted(flaky), "pytest_k_expression": marker_expr}
