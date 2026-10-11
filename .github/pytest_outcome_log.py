"""Record every test's outcome under its own node id, for the CI test check.

CI loads this plugin into each shard of the Python tests:

    PYTHONPATH=.github pytest -p pytest_outcome_log --outcome-log=outcomes-1.jsonl ...

and ``.github/check_test_shards.py`` reads the files. They replace the JUnit
XML the check used to read, which loses two things the check needs:

- JUnit renames a test (``a/b.py::t`` becomes class ``a.b``, name ``t``), so
  two different node ids can share a JUnit name. Here each record carries the
  node id pytest collected, unchanged.
- JUnit writes a non-strict expected failure that passed (an XPASS) as an
  ordinary pass. Here it is ``xpassed``, so the check can reject a stale
  ``xfail`` marker that no longer protects anything.

Each line is a JSON object with ``nodeid``, ``outcome`` and ``reason``:

- ``passed``, ``failed``, ``skipped``, ``xfailed`` or ``xpassed`` for a test.
  ``failed`` covers a failed or erroring setup, call or teardown and a strict
  XPASS. ``reason`` is the skip or xfail reason, else empty.
- ``collect-skipped`` or ``collect-failed`` for a module or other collector
  that pytest skipped or could not collect, such as a module-level
  ``pytest.skip(allow_module_level=True)`` or ``importorskip``. Every shard
  collects the whole suite, so these appear once per shard.
- ``incomplete`` for a test that reported no teardown or no outcome, for
  example because the run was interrupted.

With pytest-xdist the controller writes the file from the reports the workers
send it; the workers write nothing.

Standard library only, like the check.
"""

import json
import os


def pytest_addoption(parser):
    parser.addoption(
        "--outcome-log",
        default=None,
        metavar="PATH",
        help="Write each test's outcome to PATH as JSON Lines.",
    )


def pytest_configure(config):
    path = config.getoption("outcome_log")
    # An xdist worker has workerinput; its reports reach the controller.
    if path and not hasattr(config, "workerinput"):
        config.pluginmanager.register(OutcomeRecorder(path), "outcome-recorder")


def skip_reason(report) -> str:
    """The reason a skipped report gives, without pytest's "Skipped: " prefix."""
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        reason = str(longrepr[2])
    else:
        reason = str(longrepr or "")
    return reason.removeprefix("Skipped: ")


class OutcomeRecorder:
    def __init__(self, path: str):
        self.path = path
        # nodeid -> {"outcome", "reason", "done"}, in report order.
        self.tests = {}
        self.collectors = {}

    def pytest_collectreport(self, report):
        if report.passed:
            return
        if report.failed:
            self.collectors[report.nodeid] = {
                "outcome": "collect-failed",
                "reason": "",
            }
        elif report.nodeid not in self.collectors:
            self.collectors[report.nodeid] = {
                "outcome": "collect-skipped",
                "reason": skip_reason(report),
            }

    def pytest_runtest_logreport(self, report):
        test = self.tests.setdefault(
            report.nodeid, {"outcome": None, "reason": "", "done": False}
        )
        wasxfail = getattr(report, "wasxfail", None)
        if report.failed:
            # A failure in any phase decides the outcome, including a failed
            # teardown after a passed call.
            test["outcome"] = "failed"
            test["reason"] = ""
        elif test["outcome"] != "failed":
            if report.skipped:
                if wasxfail is not None:
                    test["outcome"] = "xfailed"
                    test["reason"] = wasxfail.removeprefix("reason: ")
                else:
                    test["outcome"] = "skipped"
                    test["reason"] = skip_reason(report)
            elif report.when == "call" and test["outcome"] in (None, "passed"):
                # A passing call never replaces an earlier skip or expected
                # failure: with subtests (pytest 9), a skipped subtest reports
                # before the test's own passing call.
                if wasxfail is not None:
                    test["outcome"] = "xpassed"
                    test["reason"] = wasxfail.removeprefix("reason: ")
                else:
                    test["outcome"] = "passed"
        if report.when == "teardown":
            test["done"] = True

    def pytest_sessionfinish(self, session):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            for nodeid, collector in self.collectors.items():
                file.write(json.dumps({"nodeid": nodeid, **collector}) + "\n")
            for nodeid, test in self.tests.items():
                outcome = test["outcome"]
                if outcome != "failed" and (outcome is None or not test["done"]):
                    outcome = "incomplete"
                record = {
                    "nodeid": nodeid,
                    "outcome": outcome,
                    "reason": test["reason"],
                }
                file.write(json.dumps(record) + "\n")
