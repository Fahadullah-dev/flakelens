"""Parses pytest-style JUnit XML. One file is treated as one test run.

Only the shape pytest's --junitxml writer produces is supported: a
<testsuite> of <testcase classname="..." name="..."> elements, each
optionally containing a <failure> or <error> child on failure, or a
<skipped> child. Other JUnit dialects (jest, gradle) are not handled.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def test_id(testcase):
    return f"{testcase.get('classname', '')}::{testcase.get('name', '')}"


def parse_run(xml_path):
    """Returns {test_id: 'pass' | 'fail' | 'skip'} for one run file."""
    root = ET.parse(xml_path).getroot()
    testcases = root.iter("testcase")
    results = {}
    for tc in testcases:
        if tc.find("skipped") is not None:
            results[test_id(tc)] = "skip"
        elif tc.find("failure") is not None or tc.find("error") is not None:
            results[test_id(tc)] = "fail"
        else:
            results[test_id(tc)] = "pass"
    return results


def load_history(directory):
    """Returns {test_id: (runs, failures)} aggregated across all XML files in directory."""
    counts = defaultdict(lambda: [0, 0])  # [runs, failures]
    files = sorted(Path(directory).glob("*.xml"))
    for f in files:
        for tid, status in parse_run(f).items():
            if status == "skip":
                continue
            counts[tid][0] += 1
            if status == "fail":
                counts[tid][1] += 1
    return {tid: tuple(v) for tid, v in counts.items()}
