from flakelens.history import load_history

PASS_FAIL_XML = """<testsuite>
  <testcase classname="tests.test_a" name="test_ok"></testcase>
  <testcase classname="tests.test_a" name="test_bad"><failure message="boom"/></testcase>
  <testcase classname="tests.test_a" name="test_skipped"><skipped message="skip"/></testcase>
</testsuite>
"""

TAP_SAMPLE = """TAP version 13
1..3
ok 1 - tests.test_a::test_ok
not ok 2 - tests.test_a::test_bad
ok 3 - tests.test_a::test_skipped # SKIP not relevant
"""


def test_load_history_aggregates_junit_across_files_and_excludes_skips(tmp_path):
    (tmp_path / "run1.xml").write_text(PASS_FAIL_XML)
    (tmp_path / "run2.xml").write_text(PASS_FAIL_XML)
    history = load_history(tmp_path)
    assert history["tests.test_a::test_ok"] == (2, 0)
    assert history["tests.test_a::test_bad"] == (2, 2)
    assert "tests.test_a::test_skipped" not in history


def test_load_history_aggregates_tap_across_files(tmp_path):
    (tmp_path / "run1.tap").write_text(TAP_SAMPLE)
    (tmp_path / "run2.tap").write_text(TAP_SAMPLE)
    history = load_history(tmp_path)
    assert history["tests.test_a::test_ok"] == (2, 0)
    assert history["tests.test_a::test_bad"] == (2, 2)
    assert "tests.test_a::test_skipped" not in history


def test_load_history_aggregates_mixed_junit_and_tap_together(tmp_path):
    (tmp_path / "run1.xml").write_text(PASS_FAIL_XML)
    (tmp_path / "run2.tap").write_text(TAP_SAMPLE)
    history = load_history(tmp_path)
    # one failure from each format for test_bad, one run each -> 2 runs, 2 failures
    assert history["tests.test_a::test_ok"] == (2, 0)
    assert history["tests.test_a::test_bad"] == (2, 2)


def test_load_history_ignores_unrecognized_file_extensions(tmp_path):
    (tmp_path / "run1.xml").write_text(PASS_FAIL_XML)
    (tmp_path / "notes.txt").write_text("not a test report")
    history = load_history(tmp_path)
    assert history["tests.test_a::test_ok"] == (1, 0)


def test_load_history_empty_directory(tmp_path):
    assert load_history(tmp_path) == {}
