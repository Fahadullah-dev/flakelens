from flakelens.tap import parse_run

TAP_SAMPLE = """TAP version 13
1..4
ok 1 - tests.test_a::test_ok
not ok 2 - tests.test_a::test_bad
ok 3 - tests.test_a::test_skipped # SKIP not relevant
not ok 4 - tests.test_a::test_err
"""


def test_parse_run_classifies_each_status(tmp_path):
    f = tmp_path / "run1.tap"
    f.write_text(TAP_SAMPLE)
    result = parse_run(f)
    assert result["tests.test_a::test_ok"] == "pass"
    assert result["tests.test_a::test_bad"] == "fail"
    assert result["tests.test_a::test_skipped"] == "skip"
    assert result["tests.test_a::test_err"] == "fail"


def test_parse_run_falls_back_to_test_number_when_no_description(tmp_path):
    f = tmp_path / "run1.tap"
    f.write_text("TAP version 13\n1..1\nok 1\n")
    result = parse_run(f)
    assert result == {"test_1": "pass"}
