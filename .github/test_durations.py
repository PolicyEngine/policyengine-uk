"""Measure the slowest Python tests from CI logs, for shard_durations.toml.

The shards of the Test job run with ``pytest -v -n 4``, so each finished test
logs a line such as::

    2026-10-24T10:57:20.4034260Z [gw0] [  0%] PASSED path.py::test_name

GitHub stamps every line with the time it was written. A pytest-xdist worker
runs one test at a time, so the time between two consecutive lines from the
same worker is the second test's duration, set-up and tear-down included.
This reads the logs of one or more shard jobs, saved with::

    gh run view RUN --log --job JOB > RUN-K.log

averages each test's duration over the logs it appears in, and prints the
tests that took at least --min-seconds as the TOML table conftest.py reads.

Standard library only, like the other scripts here.
"""

import argparse
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime

LINE = re.compile(
    r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)Z "
    r"\[(gw\d+)\] \[\s*\d+%\] (?:PASSED|FAILED|SKIPPED|XFAIL|XPASS|ERROR) (.+?)"
    # The job's once-a-minute memory report can land on the same line.
    r"(?: memory: \d+ MB used, \d+ MB available)? *$"
)
# pytest-xdist logs this once its workers are up; a worker's first test is
# timed from here.
START = re.compile(
    r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)Z created: \d+/\d+ workers"
)


def _time(stamp: str) -> datetime:
    # Seven fractional digits: datetime reads at most six.
    whole, _, fraction = stamp.partition(".")
    return datetime.fromisoformat(f"{whole}.{(fraction + '000000')[:6]}")


def durations(lines) -> dict[str, float]:
    """Each test's duration in seconds in one shard's log."""
    start = None
    last = {}
    found = {}
    for line in lines:
        if start is None and (match := START.search(line)):
            start = _time(match[1])
        if match := LINE.search(line):
            stamp, worker, nodeid = _time(match[1]), match[2], match[3]
            previous = last.get(worker, start or stamp)
            found[nodeid] = (stamp - previous).total_seconds()
            last[worker] = stamp
    return found


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("logs", nargs="+", help="saved logs of shard jobs")
    parser.add_argument("--min-seconds", type=float, default=60)
    args = parser.parse_args(argv)
    seen = defaultdict(list)
    for path in args.logs:
        with open(path, encoding="utf-8", errors="replace") as log:
            for nodeid, seconds in durations(log).items():
                seen[nodeid].append(seconds)
    mean = {nodeid: statistics.mean(values) for nodeid, values in seen.items()}
    slow = sorted(
        ((seconds, nodeid) for nodeid, seconds in mean.items()),
        key=lambda item: (-item[0], item[1]),
    )
    print("[seconds]")
    for seconds, nodeid in slow:
        if seconds < args.min_seconds:
            break
        key = nodeid.replace("\\", "\\\\").replace('"', '\\"')
        print(f'"{key}" = {round(seconds)}')
    total = sum(mean.values()) / 60
    print(f"# {len(mean)} tests, {total:.0f} worker-minutes", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
