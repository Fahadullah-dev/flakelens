"""Parses TAP (Test Anything Protocol) output. One file is treated as one test run.

Built on tap.py (https://github.com/python-tap/tappy). TAP is a genuinely different, non-XML
format from JUnit XML - what Bats (bash test suites), Perl's native test harness, PHP via
--tap, and Node's own tap/node-tap framework produce natively.

Limitation, disclosed rather than hidden: TAP has no class/module scoping the way JUnit XML
does (no classname attribute) - only a line description. If a TAP producer emits generic or
duplicate descriptions across runs, history aggregation can conflate distinct tests under one
test_id. Point flakelens at a TAP producer that emits distinguishable descriptions.
"""

from tap.parser import Parser


def parse_run(tap_path):
    """Returns {test_id: 'pass' | 'fail' | 'skip'} for one run file."""
    results = {}
    for line in Parser().parse_file(str(tap_path)):
        if line.category != "test":
            continue
        test_id = line.description.lstrip("-").strip() or f"test_{line.number}"
        if line.skip:
            results[test_id] = "skip"
        elif line.ok:
            results[test_id] = "pass"
        else:
            results[test_id] = "fail"
    return results
