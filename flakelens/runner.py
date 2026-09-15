"""Runs a pytest suite N times and collects JUnit XML per run.

This executes arbitrary test code from the target project. It is the slow,
live counterpart to history.load_history, which only reads existing reports.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from . import history


def run_repeated(test_path, runs):
    """Runs pytest against test_path `runs` times, returns {test_id: (runs, failures)}."""
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(runs):
            report = Path(tmp) / f"run_{i:03d}.xml"
            subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), f"--junitxml={report}", "-q"],
                capture_output=True,
                timeout=300,
            )
        return history.load_history(tmp)
