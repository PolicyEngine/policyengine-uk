"""Check that the shards of the Test job ran every test once, and that it passed.

CI splits ``pytest policyengine_uk/tests`` over several runners with
``--shard K/N`` (see policyengine_uk/tests/conftest.py). Each shard records
every test's outcome with ``.github/pytest_outcome_log.py``. This script
compares those records with what an unsharded ``pytest --collect-only -q``
lists:

    python .github/check_test_shards.py --collected collected.txt \\
        --outcomes outcomes-1.jsonl outcomes-2.jsonl outcomes-3.jsonl \\
        --allowlist .github/test_outcome_allowlist.toml --mode source --data present

It fails if a collected test ran in no shard or in more than one, if a test
ran that was not collected, if a test or a module failed, and if a test was
skipped, was an expected failure or passed unexpectedly (XPASS) without an
entry in the allowlist that covers this run. So a green Test job means every
collected test passed, except the outcomes a reviewer has accepted in
``.github/test_outcome_allowlist.toml``: splitting the suite cannot drop a
test, and a test that quietly stops running turns the job red.

``--mode`` says what was tested: ``source``, the checked-out tree, or
``wheel``, an installed wheel (the release workflow). ``--data`` says whether
the run had the credentials for the microsimulation dataset. Allowlist entries
can be limited to either.

Standard library only: the job that runs it does not install the package.
"""

import argparse
import fnmatch
import json
import re
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

_COLLECTED_SUMMARY = re.compile(r"^(\d+) tests? collected\b(.*)$")
_NOTHING_COLLECTED = re.compile(r"^no tests collected\b")

TEST_OUTCOMES = {"passed", "failed", "skipped", "xfailed", "xpassed", "incomplete"}
COLLECTOR_OUTCOMES = {"collect-skipped", "collect-failed"}
# The outcomes an allowlist entry can accept. Failures never can.
ALLOWABLE_OUTCOMES = {"skipped", "xfailed", "xpassed", "collect-skipped"}
MODES = {"source", "wheel"}
DATA = {"present", "absent"}


class ShardCheckError(Exception):
    """An input that cannot be checked, as opposed to a check that failed."""


def read_collected(text: str) -> list[str]:
    """Node ids from the output of ``pytest --collect-only -q``.

    The listing is one node id per line, a blank line, then any warnings and
    ``N tests collected``. The ids found must number N, so a listing this
    cannot parse is an error, never a shorter list.
    """
    ids = []
    total = None
    listing_ended = False
    for line in text.splitlines():
        summary = _COLLECTED_SUMMARY.match(line)
        if summary:
            if "error" in summary.group(2):
                raise ShardCheckError(f"collection reported errors: {line!r}")
            total = int(summary.group(1))
        elif _NOTHING_COLLECTED.match(line):
            total = 0
        elif not line.strip():
            listing_ended = listing_ended or bool(ids)
        elif "::" in line and not listing_ended:
            ids.append(line)
    if total is None:
        raise ShardCheckError("no 'N tests collected' line in the collection listing")
    if len(ids) != total:
        raise ShardCheckError(
            f"the collection listing says {total} tests but lists {len(ids)}"
        )
    if len(set(ids)) != len(ids):
        raise ShardCheckError("the collection listing repeats a node id")
    return ids


@dataclass(frozen=True)
class Record:
    nodeid: str
    outcome: str
    reason: str = ""

    @property
    def is_collector(self) -> bool:
        return self.outcome in COLLECTOR_OUTCOMES


def read_outcomes(text: str) -> list[Record]:
    """The records one shard's outcome log holds, in order."""
    records = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as error:
            raise ShardCheckError(f"line {number} is not JSON: {error}") from None
        if not isinstance(data, dict):
            raise ShardCheckError(f"line {number} is not a JSON object")
        nodeid, outcome = data.get("nodeid"), data.get("outcome")
        reason = data.get("reason", "")
        if not isinstance(nodeid, str) or not nodeid:
            raise ShardCheckError(f"line {number} has no node id")
        if outcome not in TEST_OUTCOMES | COLLECTOR_OUTCOMES:
            raise ShardCheckError(f"line {number} has unknown outcome {outcome!r}")
        if not isinstance(reason, str):
            raise ShardCheckError(f"line {number} has a reason that is not text")
        records.append(Record(nodeid, outcome, reason))
    return records


@dataclass(frozen=True)
class Allowance:
    """One allowlist entry: an outcome other than a pass that a run may have."""

    nodeid: str
    outcome: str
    why: str
    reason: re.Pattern | None = None
    modes: frozenset = frozenset(MODES)
    data: frozenset = frozenset(DATA)

    def applies(self, mode: str, data: str) -> bool:
        return mode in self.modes and data in self.data

    def accepts(self, record: Record, mode: str, data: str) -> bool:
        return (
            self.applies(mode, data)
            and record.outcome == self.outcome
            and fnmatch.fnmatchcase(record.nodeid, self.nodeid)
            and (self.reason is None or bool(self.reason.search(record.reason)))
        )

    def describe(self) -> str:
        parts = [self.outcome, self.nodeid]
        if self.reason is not None:
            parts.append(f"reason /{self.reason.pattern}/")
        if self.modes != MODES:
            parts.append("modes " + ",".join(sorted(self.modes)))
        if self.data != DATA:
            parts.append("data " + ",".join(sorted(self.data)))
        return " ".join(parts)


def _choices(entry: dict, key: str, allowed: set, number: int) -> frozenset:
    value = entry.get(key, sorted(allowed))
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not value or not set(value) <= allowed:
        raise ShardCheckError(
            f"allowlist entry {number}: {key} must be a non-empty list of "
            f"{sorted(allowed)}, got {value!r}"
        )
    return frozenset(value)


def read_allowlist(text: str) -> list[Allowance]:
    """The entries of a TOML allowlist (see .github/test_outcome_allowlist.toml)."""
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ShardCheckError(f"the allowlist is not valid TOML: {error}") from None
    unknown = set(document) - {"allow"}
    if unknown:
        raise ShardCheckError(f"the allowlist has unknown tables {sorted(unknown)}")
    allowances = []
    for number, entry in enumerate(document.get("allow", []), start=1):
        unknown = set(entry) - {"nodeid", "outcome", "why", "reason", "modes", "data"}
        if unknown:
            raise ShardCheckError(
                f"allowlist entry {number} has unknown keys {sorted(unknown)}"
            )
        nodeid, outcome, why = (
            entry.get("nodeid"),
            entry.get("outcome"),
            entry.get("why"),
        )
        if not isinstance(nodeid, str) or not nodeid:
            raise ShardCheckError(f"allowlist entry {number} has no nodeid")
        if outcome not in ALLOWABLE_OUTCOMES:
            raise ShardCheckError(
                f"allowlist entry {number}: outcome must be one of "
                f"{sorted(ALLOWABLE_OUTCOMES)}, got {outcome!r}"
            )
        if not isinstance(why, str) or not why.strip():
            raise ShardCheckError(f"allowlist entry {number} does not say why")
        reason = entry.get("reason")
        if reason is not None:
            try:
                reason = re.compile(reason)
            except (re.error, TypeError) as error:
                raise ShardCheckError(
                    f"allowlist entry {number}: reason is not a regex: {error}"
                ) from None
        allowances.append(
            Allowance(
                nodeid=nodeid,
                outcome=outcome,
                why=why.strip(),
                reason=reason,
                modes=_choices(entry, "modes", MODES, number),
                data=_choices(entry, "data", DATA, number),
            )
        )
    return allowances


@dataclass
class Result:
    problems: list  # (title, [lines]); the check fails if any
    warnings: list  # (title, [lines]); reported only
    summary: str


def check(
    collected: list[str],
    shards: list[list[Record]],
    allowlist: list[Allowance] = (),
    mode: str = "source",
    data: str = "present",
) -> Result:
    """Compare the collected node ids with what each shard recorded."""
    if mode not in MODES or data not in DATA:
        raise ShardCheckError(f"unknown mode {mode!r} or data {data!r}")
    expected = set(collected)
    runs = Counter()
    outcomes = Counter()
    tests = []
    # A collector's outcome is the same in every shard, since each collects
    # the whole suite; keep one record per collector.
    collectors = {}
    collector_shards = Counter()
    for cases in shards:
        seen_here = set()
        for record in cases:
            if record.is_collector:
                if record.nodeid not in seen_here:
                    seen_here.add(record.nodeid)
                    collector_shards[record.nodeid] += 1
                if (
                    record.outcome == "collect-failed"
                    or record.nodeid not in collectors
                ):
                    collectors[record.nodeid] = record
            else:
                runs[record.nodeid] += 1
                outcomes[record.outcome] += 1
                tests.append(record)

    problems, warnings = [], []
    missing = sorted(nodeid for nodeid in expected if nodeid not in runs)
    if missing:
        problems.append((f"{len(missing)} collected tests ran in no shard", missing))
    repeated = sorted(nodeid for nodeid, count in runs.items() if count > 1)
    if repeated:
        problems.append((f"{len(repeated)} tests ran more than once", repeated))
    extra = sorted(nodeid for nodeid in runs if nodeid not in expected)
    if extra:
        problems.append((f"{len(extra)} tests ran but were not collected", extra))

    used = Counter()
    unaccepted = {}
    for record in [*collectors.values(), *tests]:
        if record.outcome == "passed":
            continue
        if record.outcome in {"failed", "collect-failed", "incomplete"}:
            unaccepted.setdefault(record.outcome, []).append(record)
            continue
        accepted_by = [a for a in allowlist if a.accepts(record, mode, data)]
        if accepted_by:
            for allowance in accepted_by:
                used[allowance] += 1
        else:
            unaccepted.setdefault(record.outcome, []).append(record)

    titles = {
        "failed": "tests failed",
        "collect-failed": "modules could not be collected",
        "incomplete": "tests did not finish",
        "skipped": "tests were skipped without an allowlist entry",
        "xfailed": "tests failed as expected (xfail) without an allowlist entry",
        "xpassed": (
            "tests marked xfail passed (XPASS) without an allowlist entry; "
            "remove the stale xfail marker"
        ),
        "collect-skipped": "modules were skipped without an allowlist entry",
    }
    for outcome, title in titles.items():
        records = unaccepted.get(outcome)
        if records:
            problems.append(
                (
                    f"{len(records)} {title}",
                    sorted(
                        r.nodeid + (f"  ({r.reason})" if r.reason else "")
                        for r in records
                    ),
                )
            )

    unused = [
        allowance.describe()
        for allowance in allowlist
        if allowance.applies(mode, data) and not used[allowance]
    ]
    if unused:
        warnings.append(
            (
                f"{len(unused)} allowlist entries matched nothing in this run; "
                "remove them if they are no longer needed",
                unused,
            )
        )
    uneven = sorted(
        nodeid for nodeid, count in collector_shards.items() if count != len(shards)
    )
    if uneven:
        warnings.append(
            (
                f"{len(uneven)} modules were skipped or failed at collection in "
                "some shards but not others",
                uneven,
            )
        )

    sizes = "/".join(
        str(sum(not record.is_collector for record in cases)) for cases in shards
    )
    counted = ", ".join(
        f"{outcomes[name]} {name}"
        for name in ("passed", "skipped", "xfailed", "xpassed", "failed", "incomplete")
        if outcomes[name] or name == "passed"
    )
    summary = (
        f"{len(collected)} tests collected; {len(shards)} shards ran {sizes} = "
        f"{sum(runs.values())} ({counted}); {len(collectors)} modules skipped or "
        f"failed at collection; mode {mode}, dataset {data}"
    )
    return Result(problems, warnings, summary)


def _print_section(title: str, lines: list[str]) -> None:
    print(f"\n{title}:")
    for line in lines[:50]:
        print(f"  {line}")
    if len(lines) > 50:
        print(f"  ... and {len(lines) - 50} more")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--collected",
        required=True,
        type=Path,
        help="output of an unsharded `pytest --collect-only -q`",
    )
    parser.add_argument(
        "--outcomes",
        required=True,
        nargs="+",
        type=Path,
        help="the outcome log of each shard (.github/pytest_outcome_log.py)",
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        help="TOML file of accepted skips, expected failures and XPASSes",
    )
    parser.add_argument("--mode", choices=sorted(MODES), default="source")
    parser.add_argument("--data", choices=sorted(DATA), default="present")
    args = parser.parse_args(argv)

    try:
        collected = read_collected(args.collected.read_text(encoding="utf-8"))
        shards = [
            read_outcomes(path.read_text(encoding="utf-8")) for path in args.outcomes
        ]
        allowlist = (
            read_allowlist(args.allowlist.read_text(encoding="utf-8"))
            if args.allowlist
            else []
        )
        result = check(collected, shards, allowlist, args.mode, args.data)
    except (ShardCheckError, OSError, UnicodeDecodeError) as error:
        print(f"Cannot check the shards: {error}", file=sys.stderr)
        return 2

    print(result.summary)
    for title, lines in result.problems:
        _print_section(title, lines)
    for title, lines in result.warnings:
        _print_section(f"Warning: {title}", lines)
    if result.problems:
        return 1
    print(
        "\nEvery collected test ran in exactly one shard and passed, apart from "
        "allowlisted outcomes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
