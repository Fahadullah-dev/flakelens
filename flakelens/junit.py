"""Parses pytest-style JUnit XML. One file is treated as one test run.

Built on junitparser (https://github.com/weiwei/junitparser) instead of a hand-rolled
ElementTree walker, so dialect variance across JUnit-XML producers - jest-junit, gotestsum
--junitfile, rspec_junit_formatter, PHPUnit --log-junit, Maven/Gradle Surefire, and pytest's
own writer - is handled by a library that already deals with it, not reinvented here.
junitparser.JUnitXml.fromfile() normalizes both a bare <testsuite> root and a
<testsuites>-wrapped root into the same `for suite in xml: for case in suite:` shape.
"""

from junitparser import Error, Failure, JUnitXml, Skipped


def test_id(testcase):
    return f"{testcase.classname or ''}::{testcase.name or ''}"


def parse_run(xml_path):
    """Returns {test_id: 'pass' | 'fail' | 'skip'} for one run file."""
    xml = JUnitXml.fromfile(str(xml_path))
    results = {}
    for suite in xml:
        for case in suite:
            if any(isinstance(r, Skipped) for r in case.result):
                results[test_id(case)] = "skip"
            elif any(isinstance(r, (Failure, Error)) for r in case.result):
                results[test_id(case)] = "fail"
            else:
                results[test_id(case)] = "pass"
    return results
