"""Check that the shards of the Test job ran every test exactly once.

CI splits ``pytest policyengine_uk/tests`` over several runners with
``--shard K/N`` (see policyengine_uk/tests/conftest.py). This script compares
what the shards ran with what an unsharded ``pytest --collect-only -q`` lists:

    python .github/check_test_shards.py \
        --collected collected.txt --junit junit-1.xml junit-2.xml junit-3.xml

It fails if a collected test is missing from every shard, ran in more than one,
ran without being collected, or failed. So splitting the suite cannot drop a
test without the Test job going red.

Standard library only: the job that runs it does not install the package.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ElementTree
from collections import Counter
from pathlib import Path

_COLLECTED_SUMMARY = re.compile(r"^(\d+) tests? collected\b(.*)$")
_NOTHING_COLLECTED = re.compile(r"^no tests collected\b")


class ShardCheckError(Exception):
    """An input that cannot be checked, as opposed to a check that failed."""


def junit_key(nodeid: str) -> tuple[str, str]:
    """The ``(classname, name)`` pytest gives ``nodeid`` in JUnit XML.

    Follows _pytest.junitxml.mangle_test_address; a test compares the two.
    pytest also rewrites characters that XML does not allow, such as control
    characters. Its node ids do not contain them, because it escapes them in
    parameter ids. If one ever did, the names would differ and the check
    would fail, not pass.
    """
    path, bracket, params = nodeid.partition("[")
    names = path.split("::")
    names[0] = re.sub(r"\.py$", "", names[0].replace("/", "."))
    names[-1] += bracket + params
    return ".".join(names[:-1]), names[-1]


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


def read_junit(path: Path) -> list[tuple[tuple[str, str], str]]:
    """``((classname, name), outcome)`` for each test case in a JUnit file.

    The outcome is ``failed`` for a failure or an error, else ``skipped`` for a
    skip or an expected failure, else ``passed``.
    """
    cases = []
    for case in ElementTree.parse(path).getroot().iter("testcase"):
        children = {child.tag for child in case}
        if children & {"failure", "error"}:
            outcome = "failed"
        elif "skipped" in children:
            outcome = "skipped"
        else:
            outcome = "passed"
        cases.append(((case.get("classname", ""), case.get("name", "")), outcome))
    return cases


def check(collected: list[str], shards: list[list[tuple[tuple[str, str], str]]]):
    """Compare the collected node ids with what each shard ran.

    Returns ``(problems, summary)``: ``problems`` is empty when every collected
    test ran in exactly one shard and none failed.
    """
    expected = {}
    for nodeid in collected:
        key = junit_key(nodeid)
        if key in expected:
            raise ShardCheckError(
                f"{nodeid!r} and {expected[key]!r} have the same JUnit name"
            )
        expected[key] = nodeid

    runs = Counter()
    outcomes = Counter()
    failed = []
    for number, cases in enumerate(shards, start=1):
        for key, outcome in cases:
            runs[key] += 1
            outcomes[outcome] += 1
            if outcome == "failed":
                failed.append((number, key))

    def name(key):
        return expected.get(key) or f"{key[0]}::{key[1]}"

    problems = []
    missing = sorted(expected[key] for key in expected if key not in runs)
    if missing:
        problems.append((f"{len(missing)} collected tests ran in no shard", missing))
    repeated = sorted(name(key) for key, count in runs.items() if count > 1)
    if repeated:
        problems.append((f"{len(repeated)} tests ran more than once", repeated))
    extra = sorted(name(key) for key in runs if key not in expected)
    if extra:
        problems.append((f"{len(extra)} tests ran but were not collected", extra))
    if failed:
        problems.append(
            (
                f"{len(failed)} tests failed",
                [f"shard {number}: {name(key)}" for number, key in failed],
            )
        )

    sizes = "/".join(str(len(cases)) for cases in shards)
    summary = (
        f"{len(collected)} tests collected; {len(shards)} shards ran "
        f"{sizes} = {sum(len(cases) for cases in shards)} "
        f"({outcomes['passed']} passed, {outcomes['skipped']} skipped or "
        f"expected failures, {outcomes['failed']} failed)"
    )
    return problems, summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--collected",
        required=True,
        type=Path,
        help="output of an unsharded `pytest --collect-only -q`",
    )
    parser.add_argument(
        "--junit",
        required=True,
        nargs="+",
        type=Path,
        help="the JUnit XML file of each shard",
    )
    args = parser.parse_args(argv)

    try:
        collected = read_collected(args.collected.read_text(encoding="utf-8"))
        shards = [read_junit(path) for path in args.junit]
        problems, summary = check(collected, shards)
    except (ShardCheckError, OSError, ElementTree.ParseError) as error:
        print(f"Cannot check the shards: {error}", file=sys.stderr)
        return 2

    print(summary)
    for title, names in problems:
        print(f"\n{title}:")
        for line in names[:50]:
            print(f"  {line}")
        if len(names) > 50:
            print(f"  ... and {len(names) - 50} more")
    if problems:
        return 1
    print("Every collected test ran in exactly one shard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
