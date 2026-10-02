"""Persist catalogs, claims, reviews, and publication receipts."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
from typing import Any

from policy_audit.errors import PolicyAuditError


def safe_name(value: str) -> str:
    """Convert a stable identifier to a readable file name."""

    return re.sub(r"[^A-Za-z0-9_.-]+", "__", value)


def catalog_path(state_directory: Path, version: str) -> Path:
    return state_directory / "catalogs" / f"{safe_name(version)}.json"


def write_catalog(
    state_directory: Path,
    catalog: dict[str, Any],
) -> Path:
    path = catalog_path(state_directory, catalog["release_version"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")
    return path


def read_catalog(state_directory: Path, version: str) -> dict[str, Any]:
    path = catalog_path(state_directory, version)
    if not path.exists():
        raise PolicyAuditError(
            f"No audit catalog for release {version}. Run policy-audit init first."
        )
    return json.loads(path.read_text())


def _review_directory(state_directory: Path, version: str) -> Path:
    return state_directory / "reviews" / safe_name(version)


def review_files(state_directory: Path, version: str) -> list[Path]:
    directory = _review_directory(state_directory, version)
    return sorted(directory.glob("*.json")) if directory.exists() else []


def read_reviews(state_directory: Path, version: str) -> list[dict[str, Any]]:
    return [
        json.loads(path.read_text()) for path in review_files(state_directory, version)
    ]


def follow_up_path(state_directory: Path, version: str, unit_id: str) -> Path:
    return (
        state_directory
        / "followups"
        / safe_name(version)
        / f"{safe_name(unit_id)}.json"
    )


def read_follow_ups(
    state_directory: Path,
    version: str,
    status: str = "pending",
) -> list[dict[str, Any]]:
    directory = state_directory / "followups" / safe_name(version)
    if not directory.exists():
        return []
    records = [
        json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))
    ]
    if status == "all":
        return records
    return [record for record in records if record.get("status") == status]


def enqueue_follow_up(
    state_directory: Path,
    request: dict[str, Any],
    origin_review: dict[str, Any],
) -> tuple[Path, dict[str, Any], bool]:
    """Create or augment one deduplicated follow-up for a release unit."""

    version = request["release_version"]
    unit_id = request["unit_id"]
    path = follow_up_path(state_directory, version, unit_id)
    now = datetime.now(timezone.utc).isoformat()
    evidence_by_id = {item["id"]: item for item in request["evidence"]}
    evidence_ids = request["evidence_ids"]
    origin = {
        "origin_review": {
            "unit_id": origin_review["unit_id"],
            "audited_at": origin_review["audited_at"],
        },
        "enqueued_at": now,
        "reason_code": request["reason_code"],
        "reason": request["reason"],
        "observed_model": request["observed_model"],
        "expected_policy": request["expected_policy"],
        "evidence_ids": evidence_ids,
        "evidence": [evidence_by_id[evidence_id] for evidence_id in evidence_ids],
        "model_locations": request["model_locations"],
    }
    deduplication_key = (
        origin_review["unit_id"],
        origin_review["audited_at"],
        request["reason_code"],
        request["reason"],
    )
    if path.exists():
        record = json.loads(path.read_text())
        for existing in record.get("origins", []):
            existing_review = existing.get("origin_review", {})
            existing_key = (
                existing_review.get("unit_id"),
                existing_review.get("audited_at"),
                existing.get("reason_code"),
                existing.get("reason"),
            )
            if existing_key == deduplication_key:
                return path, record, True
        record.setdefault("origins", []).append(origin)
        if record.get("status") != "pending":
            record["status"] = "pending"
            record["reopened_at"] = now
        record["updated_at"] = now
    else:
        record = {
            "release_version": version,
            "unit_id": unit_id,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "origins": [origin],
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path, record, False


def close_follow_up(
    state_directory: Path,
    version: str,
    unit_id: str,
    reason: str,
) -> tuple[Path, dict[str, Any]]:
    path = follow_up_path(state_directory, version, unit_id)
    if not path.exists():
        raise PolicyAuditError(
            f"No follow-up exists for {unit_id} in release {version}"
        )
    record = json.loads(path.read_text())
    if record.get("status") != "pending":
        raise PolicyAuditError(
            f"Follow-up for {unit_id} is already {record.get('status', 'unknown')}"
        )
    now = datetime.now(timezone.utc).isoformat()
    record.update(
        {
            "status": "closed",
            "updated_at": now,
            "closed_at": now,
            "close_reason": reason,
        }
    )
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path, record


def _resolve_follow_up(
    state_directory: Path,
    review: dict[str, Any],
    review_path: Path,
) -> None:
    path = follow_up_path(
        state_directory,
        review["release_version"],
        review["unit_id"],
    )
    if not path.exists():
        return
    record = json.loads(path.read_text())
    if record.get("status") != "pending":
        return
    now = datetime.now(timezone.utc).isoformat()
    record.update(
        {
            "status": "resolved",
            "updated_at": now,
            "resolved_at": now,
            "resolved_by_review": {
                "unit_id": review["unit_id"],
                "audited_at": review["audited_at"],
                "conclusion": review.get("conclusion"),
                "path": str(review_path),
            },
        }
    )
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def record_review(state_directory: Path, review: dict[str, Any]) -> Path:
    version = review["release_version"]
    unit_name = safe_name(review["unit_id"])
    audited_at = review["audited_at"]
    directory = _review_directory(state_directory, version)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{unit_name}__{safe_name(audited_at)}.json"
    if path.exists():
        raise PolicyAuditError(f"Review record already exists: {path}")
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    claim_path(state_directory, version, review["unit_id"]).unlink(missing_ok=True)
    _resolve_follow_up(state_directory, review, path)
    for follow_up in review.get("follow_ups", []):
        enqueue_follow_up(
            state_directory,
            {
                **follow_up,
                "release_version": version,
                "evidence": review["evidence"],
            },
            review,
        )
    return path


def claim_path(state_directory: Path, version: str, unit_id: str) -> Path:
    return (
        state_directory / "claims" / safe_name(version) / f"{safe_name(unit_id)}.json"
    )


def _active_claims(state_directory: Path, version: str) -> set[str]:
    directory = state_directory / "claims" / safe_name(version)
    if not directory.exists():
        return set()
    now = datetime.now(timezone.utc)
    active: set[str] = set()
    for path in directory.glob("*.json"):
        try:
            claim = json.loads(path.read_text())
            expiry = datetime.fromisoformat(claim["expires_at"])
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
        if expiry > now:
            active.add(claim["unit_id"])
    return active


def _latest_reviews_by_unit(
    state_directory: Path,
    version: str,
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for review in read_reviews(state_directory, version):
        unit_id = review["unit_id"]
        if (
            unit_id not in latest
            or review["audited_at"] > latest[unit_id]["audited_at"]
        ):
            latest[unit_id] = review
    return latest


def select_next_unit(
    state_directory: Path,
    catalog: dict[str, Any],
    scope: str = "policy",
    create_claim: bool = True,
    claim_minutes: int = 60,
) -> dict[str, Any]:
    """Return the next unchecked or least recently checked audit unit."""

    included = {
        "policy": {"policy_rule", "program_formula"},
        "all": None,
        "parameters": {"policy_rule"},
        "variables": {"program_formula"},
    }
    if scope not in included:
        raise PolicyAuditError(f"Unknown audit scope: {scope}")
    allowed = included[scope]
    latest = _latest_reviews_by_unit(
        state_directory,
        catalog["release_version"],
    )
    active_claims = _active_claims(state_directory, catalog["release_version"])
    candidates = [
        unit
        for unit in catalog["units"]
        if (allowed is None or unit["classification"] in allowed)
        and unit["unit_id"] not in active_claims
    ]
    if not candidates:
        raise PolicyAuditError(f"No unclaimed units remain in scope {scope}")

    candidate_by_id = {unit["unit_id"]: unit for unit in candidates}
    reason_priority = {
        "suspected_incorrect_in_release": 0,
        "suspected_superseded_since_release": 0,
        "dependency_review": 1,
    }
    pending_follow_ups = [
        follow_up
        for follow_up in read_follow_ups(
            state_directory,
            catalog["release_version"],
        )
        if follow_up["unit_id"] in candidate_by_id
    ]
    if pending_follow_ups:
        pending_follow_ups.sort(
            key=lambda follow_up: (
                min(
                    reason_priority.get(origin.get("reason_code"), 2)
                    for origin in (follow_up.get("origins") or [{}])
                ),
                follow_up["created_at"],
                follow_up["unit_id"],
            )
        )
        selected_follow_up = pending_follow_ups[0]
        selected = candidate_by_id[selected_follow_up["unit_id"]]
        selection_reason = "audit_follow_up"
    else:
        selected_follow_up = None
        unchecked = [unit for unit in candidates if unit["unit_id"] not in latest]
        if unchecked:
            unchecked.sort(
                key=lambda unit: (
                    unit["model_last_modified_at"] is not None,
                    unit["model_last_modified_at"] or date.min.isoformat(),
                    unit["unit_id"],
                )
            )
            selected = unchecked[0]
            selection_reason = "oldest_unchecked"
        else:
            candidates.sort(
                key=lambda unit: (
                    latest[unit["unit_id"]]["audited_at"],
                    unit["unit_id"],
                )
            )
            selected = candidates[0]
            selection_reason = "least_recently_checked"

    result = dict(selected)
    result["last_checked_at"] = latest.get(selected["unit_id"], {}).get("audited_at")
    result["selection_reason"] = selection_reason
    if selected_follow_up:
        result["follow_up"] = selected_follow_up
    if create_claim:
        now = datetime.now(timezone.utc)
        claim = {
            "release_version": catalog["release_version"],
            "unit_id": selected["unit_id"],
            "claimed_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=claim_minutes)).isoformat(),
            "claimed_by": os.environ.get("USER", "unknown"),
        }
        path = claim_path(
            state_directory,
            catalog["release_version"],
            selected["unit_id"],
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(claim, indent=2, sort_keys=True) + "\n")
        result["claim"] = claim
    return result


def publication_path(
    state_directory: Path,
    version: str,
    unit_id: str,
) -> Path:
    return (
        state_directory
        / "publications"
        / safe_name(version)
        / f"{safe_name(unit_id)}.json"
    )


def read_publication(
    state_directory: Path,
    version: str,
    unit_id: str,
) -> dict[str, Any] | None:
    path = publication_path(state_directory, version, unit_id)
    return json.loads(path.read_text()) if path.exists() else None


def record_publication(
    state_directory: Path,
    version: str,
    unit_id: str,
    publication: dict[str, Any],
) -> Path:
    path = publication_path(state_directory, version, unit_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(publication, indent=2, sort_keys=True) + "\n")
    return path
