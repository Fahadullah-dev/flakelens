from flakelens.junit import parse_run

PASS_FAIL_XML = """<testsuite>
  <testcase classname="tests.test_a" name="test_ok"></testcase>
  <testcase classname="tests.test_a" name="test_bad"><failure message="boom"/></testcase>
  <testcase classname="tests.test_a" name="test_err"><error message="boom"/></testcase>
  <testcase classname="tests.test_a" name="test_skipped"><skipped message="skip"/></testcase>
</testsuite>
"""

TESTSUITES_WRAPPED_XML = """<testsuites>
<testsuite name="suite_a">
  <testcase classname="tests.test_a" name="test_ok"></testcase>
</testsuite>
<testsuite name="suite_b">
  <testcase classname="tests.test_b" name="test_bad"><failure message="boom"/></testcase>
</testsuite>
</testsuites>
"""


def test_parse_run_classifies_each_status(tmp_path):
    f = tmp_path / "run1.xml"
    f.write_text(PASS_FAIL_XML)
    result = parse_run(f)
    assert result["tests.test_a::test_ok"] == "pass"
    assert result["tests.test_a::test_bad"] == "fail"
    assert result["tests.test_a::test_err"] == "fail"
    assert result["tests.test_a::test_skipped"] == "skip"


def test_parse_run_handles_testsuites_wrapped_root(tmp_path):
    f = tmp_path / "run1.xml"
    f.write_text(TESTSUITES_WRAPPED_XML)
    result = parse_run(f)
    assert result["tests.test_a::test_ok"] == "pass"
    assert result["tests.test_b::test_bad"] == "fail"
