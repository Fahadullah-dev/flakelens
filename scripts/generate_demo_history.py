"""Regenerates examples/history/*.xml, the fixture data for the README demo.

Each file simulates one CI run's pytest --junitxml output. The per-test
failure probabilities below are fixed and seeded, so the demo output in the
README is reproducible: rerun this script and you get the same files back.
"""

import random
from pathlib import Path

RUNS = 30
OUT_DIR = Path(__file__).parent.parent / "examples" / "history"

# test_id -> probability of failing on a given run
TESTS = {
    "tests.test_auth::test_login_redirects": 0.0,       # stable pass
    "tests.test_auth::test_expired_token": 1.0,          # broken, always fails
    "tests.test_payments::test_webhook_retry": 0.35,     # flaky
    "tests.test_payments::test_currency_round": 0.0,     # stable pass
    "tests.test_search::test_pagination_order": 0.12,    # mildly flaky
    "tests.test_search::test_empty_query": 0.0,          # stable pass
}

TESTCASE_TMPL = '    <testcase classname="{classname}" name="{name}">{body}</testcase>\n'


def render(seed):
    rng = random.Random(seed)
    lines = ["<testsuite>\n"]
    for tid, p_fail in TESTS.items():
        classname, name = tid.split("::")
        failed = rng.random() < p_fail
        body = '<failure message="assertion failed"/>' if failed else ""
        lines.append(TESTCASE_TMPL.format(classname=classname, name=name, body=body))
    lines.append("</testsuite>\n")
    return "".join(lines)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.xml"):
        old.unlink()
    for i in range(RUNS):
        (OUT_DIR / f"run_{i:02d}.xml").write_text(render(seed=1000 + i))
    print(f"wrote {RUNS} run files to {OUT_DIR}")


if __name__ == "__main__":
    main()
