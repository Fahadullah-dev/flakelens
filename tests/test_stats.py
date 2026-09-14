from flakelens.stats import classify


def test_half_failing_is_flaky():
    v = classify(runs=20, failures=10)
    assert v.status == "flaky"


def test_never_failing_is_stable():
    v = classify(runs=20, failures=0)
    assert v.status == "stable-pass"


def test_always_failing_is_broken_not_flaky():
    v = classify(runs=20, failures=20)
    assert v.status == "broken"


def test_too_few_runs_is_insufficient_data():
    v = classify(runs=2, failures=0)
    assert v.status == "insufficient-data"


def test_three_runs_still_insufficient():
    v = classify(runs=3, failures=0)
    assert v.status == "insufficient-data"


def test_confidence_interval_widens_with_fewer_runs():
    narrow = classify(runs=100, failures=10)
    wide = classify(runs=10, failures=1)
    assert (narrow.ci_high - narrow.ci_low) < (wide.ci_high - wide.ci_low)
