"""Uses pytest's own pytester fixture - the standard, official way to test a pytest plugin
end-to-end by running a real sub-pytest process - rather than unit-testing the hooks in
isolation."""

SAMPLE_TEST = """
def test_ok():
    assert True

def test_bad():
    assert False
"""


def test_without_flag_nothing_is_written(pytester):
    pytester.makepyfile(test_sample=SAMPLE_TEST)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=1)
    assert not (pytester.path / ".flakelens").exists()
    # "plugins: flakelens-x.y.z" in the session header is expected and fine (it's just
    # discovered, not enabled) - what must NOT appear is the plugin's own report output
    result.stdout.no_fnmatch_line("*flakelens: flaky tests detected*")


def test_flag_writes_history_file(pytester):
    pytester.makepyfile(test_sample=SAMPLE_TEST)
    result = pytester.runpytest("--flakelens")
    result.assert_outcomes(passed=1, failed=1)
    history_dir = pytester.path / ".flakelens" / "history"
    assert history_dir.exists()
    assert len(list(history_dir.glob("run_*.xml"))) == 1


def test_ini_option_enables_without_flag(pytester):
    pytester.makepyfile(test_sample=SAMPLE_TEST)
    pytester.makepyprojecttoml("""
        [tool.pytest.ini_options]
        flakelens_enabled = true
    """)
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=1)
    assert (pytester.path / ".flakelens" / "history").exists()


def test_written_history_is_readable_by_flakelens_junit_parser(pytester):
    pytester.makepyfile(test_sample=SAMPLE_TEST)
    pytester.runpytest("--flakelens")
    history_dir = pytester.path / ".flakelens" / "history"
    run_file = next(history_dir.glob("run_*.xml"))

    from flakelens.junit import parse_run
    result = parse_run(run_file)
    assert result["test_sample::test_ok"] == "pass"
    assert result["test_sample::test_bad"] == "fail"


def test_summary_reported_once_enough_runs_show_flakiness(pytester):
    pytester.makepyfile(test_sample="""
        import os
        def test_flaky():
            assert os.environ.get("SHOULD_PASS") == "1"
    """)
    for i in range(6):
        import os
        os.environ["SHOULD_PASS"] = "1" if i % 2 == 0 else "0"
        result = pytester.runpytest("--flakelens")
    del os.environ["SHOULD_PASS"]
    result.stdout.fnmatch_lines(["*flakelens: flaky tests detected*", "*test_flaky*"])


def test_class_method_nodeid_matches_native_junitxml_convention(pytester):
    pytester.makepyfile(test_sample="""
        class TestGroup:
            def test_method(self):
                assert True
    """)
    pytester.runpytest("--flakelens")
    history_dir = pytester.path / ".flakelens" / "history"
    run_file = next(history_dir.glob("run_*.xml"))

    from flakelens.junit import parse_run
    result = parse_run(run_file)
    assert "test_sample.TestGroup::test_method" in result
