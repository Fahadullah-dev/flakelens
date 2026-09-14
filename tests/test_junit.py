from flakelens.junit import load_history, parse_run

PASS_FAIL_XML = """<testsuite>
  <testcase classname="tests.test_a" name="test_ok"></testcase>
  <testcase classname="tests.test_a" name="test_bad"><failure message="boom"/></testcase>
  <testcase classname="tests.test_a" name="test_err"><error message="boom"/></testcase>
  <testcase classname="tests.test_a" name="test_skipped"><skipped message="skip"/></testcase>
</testsuite>
"""


def test_parse_run_classifies_each_status(tmp_path):
    f = tmp_path / "run1.xml"
    f.write_text(PASS_FAIL_XML)
    result = parse_run(f)
    assert result["tests.test_a::test_ok"] == "pass"
    assert result["tests.test_a::test_bad"] == "fail"
    assert result["tests.test_a::test_err"] == "fail"
    assert result["tests.test_a::test_skipped"] == "skip"


def test_load_history_aggregates_across_files_and_excludes_skips(tmp_path):
    (tmp_path / "run1.xml").write_text(PASS_FAIL_XML)
    (tmp_path / "run2.xml").write_text(PASS_FAIL_XML)
    history = load_history(tmp_path)
    assert history["tests.test_a::test_ok"] == (2, 0)
    assert history["tests.test_a::test_bad"] == (2, 2)
    assert "tests.test_a::test_skipped" not in history
