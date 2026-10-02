"""Validate structured audit reviews and render cited GitHub issues."""

from __future__ import annotations

from datetime import date
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from policy_audit.errors import PolicyAuditError, ReviewValidationError
from policy_audit.yaml_utils import load_yaml


CONCLUSIONS = {
    "current",
    "incorrect_in_release",
    "superseded_since_release",
    "announced_not_enacted",
    "insufficient_evidence",
    "not_official_policy_rule",
    "program_mapping_required",
}
ISSUE_CONCLUSIONS = {"incorrect_in_release", "superseded_since_release"}


def load_structured_file(path: Path) -> dict[str, Any]:
    try:
        data = load_yaml(path.read_text())
    except (OSError, yaml.YAMLError) as error:
        raise PolicyAuditError(
            f"Could not load structured file {path}: {error}"
        ) from error
    if not isinstance(data, dict):
        raise PolicyAuditError(f"Structured file must contain an object: {path}")
    return data


def load_official_source_registry() -> dict[str, Any]:
    resource = files("policy_audit").joinpath("official_sources.yaml")
    data = load_yaml(resource.read_text()) or {}
    return data


def _official_hostname(hostname: str, registry: dict[str, Any]) -> bool:
    hostname = hostname.lower().rstrip(".")
    exact = {domain.lower() for domain in registry.get("domains", [])}
    suffixes = tuple(suffix.lower() for suffix in registry.get("domain_suffixes", []))
    return hostname in exact or any(hostname.endswith(suffix) for suffix in suffixes)


def _validate_url(
    url: str,
    field_name: str,
    registry: dict[str, Any],
    errors: list[str],
) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        errors.append(f"{field_name} must be an absolute HTTPS URL")
        return
    if not _official_hostname(parsed.hostname, registry):
        errors.append(f"{field_name} is not an approved official source: {url}")


def _required_string(
    value: dict[str, Any],
    field_name: str,
    location: str,
    errors: list[str],
) -> str:
    result = value.get(field_name)
    if not isinstance(result, str) or not result.strip():
        errors.append(f"{location}.{field_name} must be a non-empty string")
        return ""
    return result.strip()


def _validate_evidence(
    review: dict[str, Any],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    registry = load_official_source_registry()
    evidence_items = review.get("evidence")
    if not isinstance(evidence_items, list) or not evidence_items:
        errors.append("evidence must contain at least one official source")
        return {}
    evidence: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(evidence_items):
        location = f"evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{location} must be an object")
            continue
        evidence_id = _required_string(item, "id", location, errors)
        for field_name in (
            "organisation",
            "authority_type",
            "title",
            "accessed_at",
            "locator",
        ):
            _required_string(item, field_name, location, errors)
        url = _required_string(item, "url", location, errors)
        final_url = _required_string(item, "final_url", location, errors)
        if url:
            _validate_url(url, f"{location}.url", registry, errors)
        if final_url:
            _validate_url(final_url, f"{location}.final_url", registry, errors)
        if evidence_id:
            if evidence_id in evidence:
                errors.append(f"Duplicate evidence id: {evidence_id}")
            evidence[evidence_id] = item
    return evidence


def _validate_evidence_ids(
    ids: Any,
    location: str,
    evidence: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if not isinstance(ids, list) or not ids:
        errors.append(f"{location} must contain at least one evidence id")
        return
    unknown = [evidence_id for evidence_id in ids if evidence_id not in evidence]
    if unknown:
        errors.append(f"{location} contains unknown evidence ids: {unknown}")


def validate_review(
    review: dict[str, Any],
    catalog: dict[str, Any],
    release_root: Path,
) -> None:
    """Validate a review before recording or publication."""

    errors: list[str] = []
    version = _required_string(review, "release_version", "review", errors)
    if version and version != catalog["release_version"]:
        errors.append(
            f"Review release {version} does not match catalog release "
            f"{catalog['release_version']}"
        )
    unit_id = _required_string(review, "unit_id", "review", errors)
    units = {unit["unit_id"]: unit for unit in catalog["units"]}
    if unit_id and unit_id not in units:
        errors.append(f"Unknown audit unit: {unit_id}")
    audited_at = _required_string(review, "audited_at", "review", errors)
    if audited_at:
        try:
            date.fromisoformat(audited_at)
        except ValueError:
            errors.append("review.audited_at must use YYYY-MM-DD")
    conclusion = _required_string(review, "conclusion", "review", errors)
    if conclusion and conclusion not in CONCLUSIONS:
        errors.append(f"Unknown conclusion: {conclusion}")
    summary = _required_string(review, "summary", "review", errors)
    if summary and "\n\n" in summary:
        errors.append("review.summary must be one paragraph")
    for field_name in ("periods_reviewed", "jurisdictions"):
        value = review.get(field_name)
        if not isinstance(value, list) or not value:
            errors.append(f"review.{field_name} must be a non-empty list")

    evidence = _validate_evidence(review, errors)
    _validate_evidence_ids(
        review.get("summary_evidence_ids"),
        "review.summary_evidence_ids",
        evidence,
        errors,
    )

    findings = review.get("findings", [])
    if not isinstance(findings, list):
        errors.append("review.findings must be a list")
        findings = []
    if conclusion in ISSUE_CONCLUSIONS and not findings:
        errors.append(f"Conclusion {conclusion} requires at least one finding")
    for finding_index, finding in enumerate(findings):
        location = f"findings[{finding_index}]"
        if not isinstance(finding, dict):
            errors.append(f"{location} must be an object")
            continue
        _required_string(finding, "statement", location, errors)
        _validate_evidence_ids(
            finding.get("evidence_ids"),
            f"{location}.evidence_ids",
            evidence,
            errors,
        )
        parts = finding.get("implementation_parts")
        if conclusion in ISSUE_CONCLUSIONS and (
            not isinstance(parts, list) or not parts
        ):
            errors.append(f"{location}.implementation_parts must not be empty")
            continue
        for part_index, part in enumerate(parts or []):
            part_location = f"{location}.implementation_parts[{part_index}]"
            if not isinstance(part, dict):
                errors.append(f"{part_location} must be an object")
                continue
            _required_string(part, "description", part_location, errors)
            _validate_evidence_ids(
                part.get("evidence_ids"),
                f"{part_location}.evidence_ids",
                evidence,
                errors,
            )
            targets = part.get("code_reference_targets")
            if conclusion in ISSUE_CONCLUSIONS and (
                not isinstance(targets, list) or not targets
            ):
                errors.append(
                    f"{part_location}.code_reference_targets must not be empty"
                )
                continue
            for target_index, target in enumerate(targets or []):
                target_location = (
                    f"{part_location}.code_reference_targets[{target_index}]"
                )
                if not isinstance(target, dict):
                    errors.append(f"{target_location} must be an object")
                    continue
                source_path = _required_string(target, "path", target_location, errors)
                _required_string(target, "location", target_location, errors)
                _validate_evidence_ids(
                    target.get("evidence_ids"),
                    f"{target_location}.evidence_ids",
                    evidence,
                    errors,
                )
                if source_path:
                    allowed_prefixes = (
                        "policyengine_uk/parameters/",
                        "policyengine_uk/variables/",
                    )
                    if not source_path.startswith(allowed_prefixes):
                        errors.append(
                            f"{target_location}.path must identify a parameter or "
                            "variable source file"
                        )
                    elif not (release_root / source_path).is_file():
                        errors.append(
                            f"{target_location}.path does not exist in release {version}"
                        )

    if conclusion in ISSUE_CONCLUSIONS:
        _required_string(review, "issue_title", "review", errors)
    if errors:
        raise ReviewValidationError("\n".join(f"- {error}" for error in errors))


def _citation_links(
    evidence_ids: list[str],
    evidence: dict[str, dict[str, Any]],
) -> str:
    links = []
    for evidence_id in evidence_ids:
        source = evidence[evidence_id]
        links.append(
            f"[{source['title']}]({source['final_url']}) ({source['locator']})"
        )
    return "; ".join(links)


def render_issue(review: dict[str, Any], catalog: dict[str, Any]) -> tuple[str, str]:
    """Render a validated review as a cited GitHub issue."""

    evidence = {item["id"]: item for item in review["evidence"]}
    unit = next(
        item for item in catalog["units"] if item["unit_id"] == review["unit_id"]
    )
    lines = [
        "## Summary",
        "",
        f"{review['summary']} {_citation_links(review['summary_evidence_ids'], evidence)}",
        "",
        "## Audited model surface",
        "",
        f"- Audited release: `policyengine-uk {review['release_version']}`",
        f"- Audit unit: `{review['unit_id']}`",
        f"- Last model modification: {unit['model_last_modified_at'] or 'unknown'}",
        f"- Audit date: {review['audited_at']}",
        f"- Periods reviewed: {', '.join(map(str, review['periods_reviewed']))}",
        f"- Jurisdictions: {', '.join(review['jurisdictions'])}",
        "",
        "## Findings and implementation parts",
        "",
    ]
    for finding_index, finding in enumerate(review.get("findings", []), start=1):
        lines.extend(
            [
                f"### {finding_index}. {finding['statement']}",
                "",
                f"Sources: {_citation_links(finding['evidence_ids'], evidence)}",
                "",
            ]
        )
        for part in finding.get("implementation_parts", []):
            citations = _citation_links(part["evidence_ids"], evidence)
            lines.append(f"- [ ] {part['description']} {citations}")
            for target in part.get("code_reference_targets", []):
                target_citations = _citation_links(target["evidence_ids"], evidence)
                lines.append(
                    f"  - Add or update `reference` at `{target['path']}` → "
                    f"`{target['location']}` using {target_citations}."
                )
        lines.append("")
    if review.get("uncertainties"):
        lines.extend(
            [
                "## Uncertainties and exclusions",
                "",
                review["uncertainties"],
                "",
            ]
        )
    title = review.get("issue_title") or (
        f"Policy audit: {review['unit_id']} in {review['release_version']}"
    )
    return title, "\n".join(lines).rstrip() + "\n"
