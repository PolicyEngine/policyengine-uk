"""Command line: ``measure`` one checkout, then ``compare`` two measurements.

    python -m policyengine_uk.utils.aggregate_impact measure --label head \\
        --pin policyengine_uk/tests/certified_dataset.yaml \\
        --reforms policyengine_uk/tests/microsimulation/reforms_config.yaml \\
        --out out/head
    python -m policyengine_uk.utils.aggregate_impact compare \\
        --base out/base --head out/head --markdown comment.md --summary summary.json

``measure`` exits 1 if the measurement crashed, after writing a result that
records the crash; ``compare`` exits 1 when the change fails the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

import yaml

from . import TOOL_SCHEMA


def _sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cmd_measure(args) -> int:
    from .dataset import load_pin, materialise, verify_file
    from .measure import write_result

    provenance = {
        "git_sha": args.git_sha,
        "git_ref": args.git_ref,
        "tool": str(Path(__file__).resolve().parent),
    }
    try:
        from .measure import measure, tool_digest
        from .partition import default_partition_path, load_partition
        from .spec import DEFAULT_SPEC_PATH, load_spec

        provenance["tool_sha256"] = tool_digest()
        provenance["metrics_version"] = (
            f"{TOOL_SCHEMA}+{provenance['tool_sha256'][:16]}"
        )

        spec_path = Path(args.spec) if args.spec else DEFAULT_SPEC_PATH
        spec = load_spec(spec_path, years=args.years)
        provenance["spec_sha256"] = _sha256(spec_path)

        pin = load_pin(args.pin)
        if args.dataset_file:
            dataset_path = Path(args.dataset_file)
            verified = verify_file(dataset_path, pin.sha256)
        else:
            dataset_path = materialise(pin)
            verified = pin.sha256
        provenance["dataset"] = {**pin.as_dict(), "verified_sha256": verified}

        if args.partition:
            partition_path, partition_source = Path(args.partition), "given"
        else:
            partition_path = default_partition_path()
            partition_source = "measured model"
            if partition_path is None:
                if not args.fallback_partition:
                    raise FileNotFoundError(
                        "the measured policyengine_uk ships no fiscal partition; "
                        "pass --fallback-partition"
                    )
                partition_path, partition_source = (
                    Path(args.fallback_partition),
                    "fallback",
                )
        partition = load_partition(partition_path)
        provenance["partition_source"] = partition_source

        reforms = []
        if args.reforms:
            with open(args.reforms) as f:
                reforms = (yaml.safe_load(f) or {}).get("reforms", [])
            provenance["reforms_sha256"] = _sha256(args.reforms)

        from policyengine_uk import Microsimulation

        sim = Microsimulation(dataset=str(dataset_path))
        dataset_object = sim.dataset

        def factory(reform=None):
            return Microsimulation(dataset=dataset_object, reform=reform or None)

        result, households = measure(
            sim,
            factory,
            partition,
            spec,
            label=args.label,
            reforms=reforms,
            run_guard=not args.no_guard,
            provenance=provenance,
        )
        write_result(args.out, result, households)
        print(
            f"{args.label}: measured {len(result['metrics'])} figures in {result['timings']['total']}s"
        )
        return 0
    except Exception:  # noqa: BLE001 - recorded for the comparison, then reported
        crash = {
            "schema": TOOL_SCHEMA,
            "status": "crashed",
            "label": args.label,
            "provenance": provenance,
            "error": traceback.format_exc(),
        }
        write_result(args.out, crash)
        print(crash["error"], file=sys.stderr)
        return 1


def cmd_compare(args) -> int:
    from .compare import compare
    from .measure import read_result
    from .render import render
    from .spec import DEFAULT_SPEC_PATH, load_spec

    spec = load_spec(Path(args.spec) if args.spec else DEFAULT_SPEC_PATH)
    base, base_households = read_result(args.base) if args.base else (None, None)
    head, head_households = read_result(args.head)
    summary = compare(
        base,
        head,
        spec,
        base_households=base_households,
        head_households=head_households,
        strict=args.strict,
    )
    markdown = render(summary, spec, context={"run_url": args.run_url})
    if args.markdown:
        Path(args.markdown).write_text(markdown)
    if args.summary:
        with open(args.summary, "w") as f:
            json.dump(summary, f, indent=1, allow_nan=True, default=str)
    print(f"aggregate impact: {summary['status']}")
    for failure in summary["failures"]:
        print(f"FAIL: {failure}")
    return 1 if summary["status"] == "fail" else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m policyengine_uk.utils.aggregate_impact"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    m = sub.add_parser("measure", help="measure one model checkout")
    m.add_argument("--label", required=True)
    m.add_argument("--pin", required=True, help="dataset pin YAML")
    m.add_argument("--dataset-file", help="local copy of the pinned file (verified)")
    m.add_argument("--partition", help="fiscal partition YAML to use")
    m.add_argument(
        "--fallback-partition",
        help="partition to use if the measured model ships none",
    )
    m.add_argument("--spec", help="report spec YAML")
    m.add_argument("--years", help="override the horizon, e.g. 2025-2031")
    m.add_argument("--reforms", help="reform regression YAML (a 'reforms' list)")
    m.add_argument("--git-sha", default="")
    m.add_argument("--git-ref", default="")
    m.add_argument(
        "--no-guard", action="store_true", help="skip the counted-once check"
    )
    m.add_argument("--out", required=True)
    m.set_defaults(func=cmd_measure)

    c = sub.add_parser("compare", help="compare a base and a head measurement")
    c.add_argument("--base")
    c.add_argument("--head", required=True)
    c.add_argument("--spec")
    c.add_argument("--markdown")
    c.add_argument("--summary")
    c.add_argument("--run-url", default="")
    c.add_argument(
        "--strict", action="store_true", help="fail on checks failing on both sides"
    )
    c.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
