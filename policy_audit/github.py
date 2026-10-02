"""Publish validated audit findings to GitHub without duplicate issues."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

from policy_audit.errors import PolicyAuditError
from policy_audit.ledger import (
    read_publication,
    record_publication,
)


def _gh(*arguments: str, input_text: str | None = None) -> Any:
    result = subprocess.run(
        ["gh", *arguments],
        input=input_text,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise PolicyAuditError(result.stderr.strip() or result.stdout.strip())
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise PolicyAuditError("GitHub returned a non-JSON response") from error


def _all_issues(repository: str) -> list[dict[str, Any]]:
    pages = _gh(
        "api",
        "--paginate",
        "--slurp",
        "--method",
        "GET",
        f"repos/{repository}/issues",
        "-f",
        "state=all",
        "-f",
        "per_page=100",
    )
    if not isinstance(pages, list):
        raise PolicyAuditError("GitHub issue listing did not return a list")
    issues: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, list):
            raise PolicyAuditError("GitHub paginated issue response was malformed")
        issues.extend(issue for issue in page if "pull_request" not in issue)
    return issues


def _matches_visible_metadata(
    issue: dict[str, Any],
    title: str,
    release_version: str,
    unit_id: str,
) -> bool:
    body = issue.get("body") or ""
    return (
        issue.get("title") == title
        and f"policyengine-uk {release_version}" in body
        and f"`{unit_id}`" in body
    )


def publish_issue(
    repository: str,
    title: str,
    body: str,
    review: dict[str, Any],
    state_directory: Path,
) -> dict[str, Any]:
    """Create one issue after direct and exhaustive duplicate checks."""

    version = review["release_version"]
    unit_id = review["unit_id"]
    recorded = read_publication(state_directory, version, unit_id)
    direct_issue = None
    if recorded:
        issue_number = recorded.get("issue_number")
        if not issue_number:
            raise PolicyAuditError("Publication record has no issue_number")
        direct_issue = _gh("api", f"repos/{repository}/issues/{issue_number}")

    matching = [
        issue
        for issue in _all_issues(repository)
        if _matches_visible_metadata(issue, title, version, unit_id)
    ]
    if len(matching) > 1:
        raise PolicyAuditError(
            f"Multiple GitHub issues match release {version} and {unit_id}"
        )
    if direct_issue:
        if not matching or matching[0].get("number") != direct_issue.get("number"):
            raise PolicyAuditError(
                "The recorded issue and exhaustive GitHub listing disagree; "
                "reconcile them before publishing."
            )
        return recorded
    if matching:
        issue = matching[0]
        publication = {
            "repository": repository,
            "issue_number": issue["number"],
            "issue_url": issue["html_url"],
            "published_at": datetime.now(timezone.utc).isoformat(),
            "reconciled_existing_issue": True,
        }
        record_publication(state_directory, version, unit_id, publication)
        return publication

    payload: dict[str, Any] = {"title": title, "body": body}
    labels = review.get("labels")
    if labels:
        payload["labels"] = labels
    issue = _gh(
        "api",
        "--method",
        "POST",
        f"repos/{repository}/issues",
        "--input",
        "-",
        input_text=json.dumps(payload),
    )
    publication = {
        "repository": repository,
        "issue_number": issue["number"],
        "issue_url": issue["html_url"],
        "published_at": datetime.now(timezone.utc).isoformat(),
        "reconciled_existing_issue": False,
    }
    record_publication(state_directory, version, unit_id, publication)
    return publication
