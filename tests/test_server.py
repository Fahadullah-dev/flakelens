from pathlib import Path

import pytest

from flakelens.server import analyze_junit_history, run_flakiness_scan, suggest_quarantine

HISTORY_DIR = Path(__file__).parent.parent / "examples" / "history"


def test_analyze_junit_history_matches_known_ground_truth():
    rows = {r["test"]: r for r in analyze_junit_history(str(HISTORY_DIR))}
    assert rows["tests.test_auth::test_expired_token"]["status"] == "broken"
    assert rows["tests.test_auth::test_login_redirects"]["status"] == "stable-pass"
    assert rows["tests.test_payments::test_webhook_retry"]["status"] == "flaky"


def test_analyze_junit_history_rejects_missing_directory():
    with pytest.raises(ValueError):
        analyze_junit_history("/no/such/directory")


def test_suggest_quarantine_only_lists_flaky_above_threshold():
    result = suggest_quarantine(str(HISTORY_DIR), threshold=0.3)
    assert result["quarantine"] == ["tests.test_payments::test_webhook_retry"]


def test_run_flakiness_scan_on_real_pytest_subprocess(tmp_path):
    test_file = tmp_path / "test_always_passes.py"
    test_file.write_text("def test_it():\n    assert True\n")
    rows = run_flakiness_scan(str(test_file), runs=5)
    assert rows[0]["status"] == "stable-pass"
    assert rows[0]["runs"] == 5
