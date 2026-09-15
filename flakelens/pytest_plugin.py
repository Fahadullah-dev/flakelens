"""Pytest plugin entry point (registered via [project.entry-points.pytest11] in
pyproject.toml). Opt-in via --flakelens or [tool.pytest.ini_options] flakelens_enabled = true
(pytest's own project-config mechanism, not a separate hand-parsed section) - a plain
`pip install flakelens` for the MCP server should not silently start writing files or
printing extra output in unrelated projects' pytest runs.

On an enabled session, accumulates this run's results as a real JUnit XML file - written via
junitparser, the same library flakelens.junit reads with, so plugin-written history round-trips
through the exact same reader as a native --junitxml file - into .flakelens/history/ in the
rootdir, then reports a flaky-test summary using the existing history.load_history +
stats.classify pipeline, unchanged.

CI note: this only works if .flakelens/history/ persists across CI runs (e.g. actions/cache
on GitHub Actions) - a single ephemeral run has nothing to accumulate against.
"""

import time
from pathlib import Path

from junitparser import Failure, JUnitXml, Skipped, TestCase, TestSuite

from . import history
from .stats import classify

HISTORY_DIRNAME = ".flakelens/history"
MAX_RUNS_KEPT = 50
_STATUS_PRIORITY = {"passed": 0, "skipped": 1, "failed": 2}


def pytest_addoption(parser):
    group = parser.getgroup("flakelens")
    group.addoption(
        "--flakelens", action="store_true", default=False,
        help="Accumulate this run into local flaky-test history and report a summary at the end.",
    )
    parser.addini(
        "flakelens_enabled", type="bool", default=False,
        help="Same as --flakelens, set project-wide (e.g. for CI) instead of per invocation.",
    )


def _enabled(config):
    return bool(config.getoption("--flakelens") or config.getini("flakelens_enabled"))


def _split_nodeid(nodeid):
    """Matches pytest's own --junitxml classname/name convention exactly (verified against a
    real pytest run), so plugin-written history is indistinguishable from a native --junitxml
    file for the same test - the two can sit in the same history directory."""
    path_part, *rest = nodeid.split("::")
    module = path_part[:-3] if path_part.endswith(".py") else path_part
    module = module.replace("/", ".").replace("\\", ".")
    if len(rest) > 1:
        return ".".join([module, *rest[:-1]]), rest[-1]
    return module, (rest[0] if rest else module)


class FlakelensPlugin:
    def __init__(self, rootdir):
        self.rootdir = Path(rootdir)
        self.outcomes = {}  # nodeid -> 'passed' | 'failed' | 'skipped'

    def pytest_runtest_logreport(self, report):
        # a test can report multiple times (setup/call/teardown); keep the worst outcome seen
        current = self.outcomes.get(report.nodeid)
        if current is None or _STATUS_PRIORITY[report.outcome] > _STATUS_PRIORITY[current]:
            self.outcomes[report.nodeid] = report.outcome

    def _write_run(self):
        suite = TestSuite("flakelens")
        for nodeid, outcome in self.outcomes.items():
            classname, name = _split_nodeid(nodeid)
            case = TestCase(name, classname)
            if outcome == "failed":
                case.result = [Failure()]
            elif outcome == "skipped":
                case.result = [Skipped()]
            suite.add_testcase(case)
        xml = JUnitXml()
        xml.add_testsuite(suite)

        history_dir = self.rootdir / HISTORY_DIRNAME
        history_dir.mkdir(parents=True, exist_ok=True)
        run_path = history_dir / f"run_{time.time_ns()}.xml"
        xml.write(str(run_path))

        runs = sorted(history_dir.glob("run_*.xml"))
        for stale in runs[:-MAX_RUNS_KEPT]:
            stale.unlink()
        return history_dir

    def report_summary(self, terminalreporter):
        if not self.outcomes:
            return
        history_dir = self._write_run()
        test_history = history.load_history(history_dir)
        flaky = [
            (tid, runs, failures)
            for tid, (runs, failures) in test_history.items()
            if classify(runs, failures).status == "flaky"
        ]
        if not flaky:
            return
        terminalreporter.write_sep("=", "flakelens: flaky tests detected")
        for tid, runs, failures in sorted(flaky, key=lambda row: -row[2] / row[1]):
            terminalreporter.write_line(f"  {tid}  {failures}/{runs} failures across recorded runs")
        terminalreporter.write_line(f"  history: {history_dir} (last {MAX_RUNS_KEPT} runs kept)")


def pytest_configure(config):
    if _enabled(config):
        config._flakelens_plugin = FlakelensPlugin(config.rootpath)
        config.pluginmanager.register(config._flakelens_plugin, "flakelens-runtime")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    plugin = getattr(config, "_flakelens_plugin", None)
    if plugin is not None:
        plugin.report_summary(terminalreporter)
