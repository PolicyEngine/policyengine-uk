"""Command-line interface for release-specific UK policy audits."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

from policy_audit.context import build_program_context, load_programs
from policy_audit.errors import PolicyAuditError
from policy_audit.github import publish_issue
from policy_audit.inventory import apply_parameter_groups, build_inventory
from policy_audit.ledger import (
    close_follow_up,
    enqueue_follow_up,
    read_catalog,
    read_follow_ups,
    read_reviews,
    record_review,
    select_next_unit,
    write_catalog,
)
from policy_audit.repository import (
    find_repository,
    prepare_release_checkout,
)
from policy_audit.reviews import (
    ISSUE_CONCLUSIONS,
    load_structured_file,
    render_issue,
    validate_follow_up_request,
    validate_review,
)


def _paths(args: argparse.Namespace) -> tuple[Path, Path]:
    repository = find_repository(Path(args.repo_path or "."))
    state_directory = (
        Path(args.state_dir).resolve()
        if args.state_dir
        else repository / ".policy-audit"
    )
    return repository, state_directory


def _checkout_for_catalog(
    repository: Path,
    state_directory: Path,
    catalog: dict[str, Any],
) -> Path:
    return prepare_release_checkout(
        repository,
        catalog["release_version"],
        state_directory,
    ).root


def _load_overrides(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    data = load_structured_file(Path(path))
    mappings = data.get("units", {})
    if not isinstance(mappings, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in mappings.items()
    ):
        raise PolicyAuditError("Program override file must contain a units mapping")
    return mappings


def _load_parameter_groups(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    data = load_structured_file(Path(path))
    groups = data.get("groups", [])
    if not isinstance(groups, list):
        raise PolicyAuditError("Parameter group file must contain a groups list")
    return groups


def _command_init(args: argparse.Namespace) -> dict[str, Any]:
    repository, state_directory = _paths(args)
    release = prepare_release_checkout(repository, args.version, state_directory)
    units = build_inventory(release)
    units = apply_parameter_groups(units, _load_parameter_groups(args.parameter_groups))
    catalog = {
        "release_version": release.version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "programs": load_programs(release.root),
        "units": [unit.to_dict() for unit in units],
    }
    path = write_catalog(state_directory, catalog)
    return {
        "release_version": release.version,
        "catalog": str(path),
        "worktree": str(release.root),
        "unit_count": len(units),
    }


def _command_next(args: argparse.Namespace) -> dict[str, Any]:
    _, state_directory = _paths(args)
    catalog = read_catalog(state_directory, args.version)
    return select_next_unit(
        state_directory,
        catalog,
        scope=args.scope,
        create_claim=not args.no_claim,
        claim_minutes=args.claim_minutes,
    )


def _command_context(args: argparse.Namespace) -> dict[str, Any]:
    repository, state_directory = _paths(args)
    catalog = read_catalog(state_directory, args.version)
    release_root = _checkout_for_catalog(repository, state_directory, catalog)
    return build_program_context(
        release_root,
        catalog,
        args.unit_id,
        _load_overrides(args.program_overrides),
    )


def _follow_up_inputs(
    args: argparse.Namespace,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    repository, state_directory = _paths(args)
    request = load_structured_file(Path(args.request))
    version = request.get("release_version")
    if not isinstance(version, str):
        raise PolicyAuditError("Follow-up request has no release_version")
    catalog = read_catalog(state_directory, version)
    release_root = _checkout_for_catalog(repository, state_directory, catalog)
    validate_follow_up_request(request, catalog, release_root)
    origin = request["origin_review"]
    matching_reviews = [
        review
        for review in read_reviews(state_directory, version)
        if review.get("unit_id") == origin["unit_id"]
        and review.get("audited_at") == origin["audited_at"]
    ]
    if not matching_reviews:
        raise PolicyAuditError(
            "The originating review is not recorded in this audit state"
        )
    return state_directory, request, matching_reviews[0]


def _command_enqueue_follow_up(args: argparse.Namespace) -> dict[str, Any]:
    state_directory, request, origin_review = _follow_up_inputs(args)
    path, record, deduplicated = enqueue_follow_up(
        state_directory,
        request,
        origin_review,
    )
    return {
        "follow_up": str(path),
        "release_version": record["release_version"],
        "unit_id": record["unit_id"],
        "status": record["status"],
        "deduplicated": deduplicated,
    }


def _command_follow_ups(args: argparse.Namespace) -> dict[str, Any]:
    _, state_directory = _paths(args)
    read_catalog(state_directory, args.version)
    records = read_follow_ups(state_directory, args.version, args.status)
    return {
        "release_version": args.version,
        "status": args.status,
        "count": len(records),
        "follow_ups": records,
    }


def _command_close_follow_up(args: argparse.Namespace) -> dict[str, Any]:
    _, state_directory = _paths(args)
    catalog = read_catalog(state_directory, args.version)
    if args.unit_id not in {unit["unit_id"] for unit in catalog["units"]}:
        raise PolicyAuditError(f"Unknown audit unit: {args.unit_id}")
    reason = args.reason.strip()
    if not reason:
        raise PolicyAuditError("A non-empty close reason is required")
    path, record = close_follow_up(
        state_directory,
        args.version,
        args.unit_id,
        reason,
    )
    return {
        "follow_up": str(path),
        "release_version": record["release_version"],
        "unit_id": record["unit_id"],
        "status": record["status"],
    }


def _review_inputs(
    args: argparse.Namespace,
) -> tuple[Path, dict[str, Any], dict[str, Any], Path]:
    repository, state_directory = _paths(args)
    review = load_structured_file(Path(args.review))
    version = review.get("release_version")
    if not isinstance(version, str):
        raise PolicyAuditError("Review has no release_version")
    catalog = read_catalog(state_directory, version)
    release_root = _checkout_for_catalog(repository, state_directory, catalog)
    validate_review(review, catalog, release_root)
    return state_directory, review, catalog, release_root


def _command_validate(args: argparse.Namespace) -> dict[str, Any]:
    _, review, _, _ = _review_inputs(args)
    return {
        "valid": True,
        "release_version": review["release_version"],
        "unit_id": review["unit_id"],
    }


def _command_record(args: argparse.Namespace) -> dict[str, Any]:
    state_directory, review, _, _ = _review_inputs(args)
    path = record_review(state_directory, review)
    return {"recorded": str(path)}


def _command_render(args: argparse.Namespace) -> dict[str, Any]:
    _, review, catalog, _ = _review_inputs(args)
    if review["conclusion"] not in ISSUE_CONCLUSIONS and not args.allow_nonissue:
        raise PolicyAuditError(
            f"Conclusion {review['conclusion']} does not normally produce an issue"
        )
    title, body = render_issue(review, catalog)
    return {"title": title, "body": body}


def _command_publish(args: argparse.Namespace) -> dict[str, Any]:
    state_directory, review, catalog, _ = _review_inputs(args)
    allowed = review["conclusion"] in ISSUE_CONCLUSIONS
    if review["conclusion"] == "announced_not_enacted" and args.allow_announced:
        allowed = True
    if not allowed:
        raise PolicyAuditError(
            f"Conclusion {review['conclusion']} is not eligible for publication"
        )
    title, body = render_issue(review, catalog)
    return publish_issue(
        args.repository,
        title,
        body,
        review,
        state_directory,
    )


def _add_storage_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-path", help="PolicyEngine UK Git repository")
    parser.add_argument(
        "--state-dir",
        help="Audit state directory; defaults to .policy-audit in the repository",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="policy-audit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Inventory an exact release")
    init_parser.add_argument("--version", required=True)
    init_parser.add_argument(
        "--parameter-groups",
        help="YAML file grouping parameters that span multiple source documents",
    )
    _add_storage_arguments(init_parser)
    init_parser.set_defaults(handler=_command_init)

    next_parser = subparsers.add_parser("next", help="Claim the next audit unit")
    next_parser.add_argument("--version", required=True)
    next_parser.add_argument(
        "--scope",
        choices=("policy", "all", "parameters", "variables"),
        default="policy",
    )
    next_parser.add_argument("--no-claim", action="store_true")
    next_parser.add_argument("--claim-minutes", type=int, default=60)
    _add_storage_arguments(next_parser)
    next_parser.set_defaults(handler=_command_next)

    context_parser = subparsers.add_parser(
        "context", help="Build bounded program context"
    )
    context_parser.add_argument("unit_id")
    context_parser.add_argument("--version", required=True)
    context_parser.add_argument("--program-overrides")
    _add_storage_arguments(context_parser)
    context_parser.set_defaults(handler=_command_context)

    follow_ups_parser = subparsers.add_parser(
        "follow-ups", help="List prioritized audit follow-ups"
    )
    follow_ups_parser.add_argument("--version", required=True)
    follow_ups_parser.add_argument(
        "--status",
        choices=("pending", "resolved", "closed", "all"),
        default="pending",
    )
    _add_storage_arguments(follow_ups_parser)
    follow_ups_parser.set_defaults(handler=_command_follow_ups)

    enqueue_parser = subparsers.add_parser(
        "enqueue-follow-up", help="Prioritize a cited related audit unit"
    )
    enqueue_parser.add_argument("request")
    _add_storage_arguments(enqueue_parser)
    enqueue_parser.set_defaults(handler=_command_enqueue_follow_up)

    close_parser = subparsers.add_parser(
        "close-follow-up", help="Close a pending audit follow-up"
    )
    close_parser.add_argument("unit_id")
    close_parser.add_argument("--version", required=True)
    close_parser.add_argument("--reason", required=True)
    _add_storage_arguments(close_parser)
    close_parser.set_defaults(handler=_command_close_follow_up)

    for name, help_text, handler in (
        ("validate", "Validate a structured review", _command_validate),
        ("record", "Record a validated review", _command_record),
        ("render-issue", "Render a review as a GitHub issue", _command_render),
    ):
        command_parser = subparsers.add_parser(name, help=help_text)
        command_parser.add_argument("review")
        if name == "render-issue":
            command_parser.add_argument("--allow-nonissue", action="store_true")
        _add_storage_arguments(command_parser)
        command_parser.set_defaults(handler=handler)

    publish_parser = subparsers.add_parser(
        "publish-issue", help="Publish one deduplicated GitHub issue"
    )
    publish_parser.add_argument("review")
    publish_parser.add_argument(
        "--repository",
        default="PolicyEngine/policyengine-uk",
        help="GitHub owner/repository",
    )
    publish_parser.add_argument("--allow-announced", action="store_true")
    _add_storage_arguments(publish_parser)
    publish_parser.set_defaults(handler=_command_publish)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.handler(args)
    except PolicyAuditError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
