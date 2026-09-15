"""Aggregates test run history across files, dispatching each file to the right format
parser by extension. Format-agnostic: junit.py and tap.py both expose the same
parse_run(path) -> {test_id: 'pass'|'fail'|'skip'} contract, so a directory mixing .xml and
.tap files aggregates together transparently - same test suite, different run sources, one
history.
"""

from collections import defaultdict
from pathlib import Path

from . import junit, tap

PARSERS = {
    ".xml": junit.parse_run,
    ".tap": tap.parse_run,
}


def load_history(directory):
    """Returns {test_id: (runs, failures)} aggregated across every recognized run file in
    directory, regardless of format."""
    counts = defaultdict(lambda: [0, 0])  # [runs, failures]
    files = sorted(
        f for f in Path(directory).iterdir()
        if f.is_file() and f.suffix in PARSERS
    )
    for f in files:
        parse_run = PARSERS[f.suffix]
        for tid, status in parse_run(f).items():
            if status == "skip":
                continue
            counts[tid][0] += 1
            if status == "fail":
                counts[tid][1] += 1
    return {tid: tuple(v) for tid, v in counts.items()}
