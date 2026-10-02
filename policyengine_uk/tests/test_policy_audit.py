from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from policy_audit.context import build_program_context, load_programs
from policy_audit.errors import ReviewValidationError
from policy_audit.github import publish_issue
from policy_audit.inventory import apply_parameter_groups, build_inventory
from policy_audit.ledger import record_review, select_next_unit
from policy_audit.repository import ReleaseCheckout, prepare_release_checkout
from policy_audit.reviews import render_issue, validate_review
from policy_audit.yaml_utils import load_yaml


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def test_prepare_release_checkout_uses_exact_version(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "test@example.com")
    _git(repository, "config", "user.name", "Test")
    _write(
        repository / "pyproject.toml",
        '[project]\nname = "policyengine-uk"\nversion = "1.2.3"\n',
    )
    _git(repository, "add", "pyproject.toml")
    _git(repository, "commit", "-qm", "release")
    _git(repository, "tag", "1.2.3")

    release = prepare_release_checkout(
        repository,
        "1.2.3",
        repository / ".audit-state",
    )

    assert release.version == "1.2.3"
    assert release.tag == "1.2.3"
    assert release.root != repository
    assert release.root.joinpath("pyproject.toml").exists()


def test_yaml_loader_preserves_year_zero_period_keys():
    assert load_yaml("values:\n  0000-01-01: false\n") == {
        "values": {"0000-01-01": False}
    }


def test_release_without_program_registry_can_still_be_inventoried(tmp_path):
    assert load_programs(tmp_path) == []


def test_inventory_groups_parameter_breakdowns_and_extracts_dependencies(
    tmp_path, monkeypatch
):
    checkout = tmp_path / "checkout"
    _write(
        checkout
        / "policyengine_uk/parameters/gov/dwp/universal_credit/standard_allowance/amount.yaml",
        """
SINGLE_YOUNG:
  values:
    2025-01-01: 300
SINGLE_OLD:
  values:
    2025-01-01: 400
metadata:
  unit: currency-GBP
""",
    )
    _write(
        checkout
        / "policyengine_uk/variables/gov/dwp/universal_credit/uc_standard_allowance.py",
        """
class uc_standard_allowance(Variable):
    defined_for = "is_uc_claimant"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.standard_allowance
        claimant_type = benunit("uc_standard_allowance_claimant_type", period)
        return p.amount[claimant_type]
""",
    )
    monkeypatch.setattr(
        "policy_audit.inventory.source_last_modified_dates",
        lambda release: {
            "policyengine_uk/parameters/gov/dwp/universal_credit/standard_allowance/amount.yaml": "2024-01-02",
            "policyengine_uk/variables/gov/dwp/universal_credit/uc_standard_allowance.py": "2024-02-03",
        },
    )
    release = ReleaseCheckout("1.0.0", "1.0.0", checkout, tmp_path)

    units = {unit.unit_id: unit for unit in build_inventory(release)}

    parameter = units["parameter:gov.dwp.universal_credit.standard_allowance.amount"]
    assert parameter.members == [
        "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD",
        "gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG",
    ]
    assert parameter.model_last_modified_at == "2024-01-02"

    variable = units["variable:uc_standard_allowance"]
    assert variable.variable_dependencies == [
        "is_uc_claimant",
        "uc_standard_allowance_claimant_type",
    ]
    assert variable.parameter_references == [
        "gov.dwp.universal_credit.standard_allowance.amount"
    ]


def test_curated_group_combines_parameter_documents():
    from policy_audit.inventory import AuditUnit

    units = [
        AuditUnit(
            unit_id="parameter:gov.example.first",
            kind="parameter",
            source_paths=["policyengine_uk/parameters/gov/example/first.yaml"],
            members=["gov.example.first.A"],
            classification="policy_rule",
            model_last_modified_at="2024-01-01",
        ),
        AuditUnit(
            unit_id="parameter:gov.example.second",
            kind="parameter",
            source_paths=["policyengine_uk/parameters/gov/example/second.yaml"],
            members=["gov.example.second.B"],
            classification="policy_rule",
            model_last_modified_at="2025-01-01",
        ),
    ]

    result = apply_parameter_groups(
        units,
        [
            {
                "unit_id": "parameter:gov.example.combined",
                "units": [
                    "parameter:gov.example.first",
                    "parameter:gov.example.second",
                ],
            }
        ],
    )

    assert len(result) == 1
    assert result[0].unit_id == "parameter:gov.example.combined"
    assert result[0].members == ["gov.example.first.A", "gov.example.second.B"]
    assert result[0].model_last_modified_at == "2025-01-01"


def test_program_context_separates_owner_and_external_consumer(tmp_path):
    release_root = tmp_path / "release"
    _write(
        release_root / "policyengine_uk/tests/test_uc.py",
        "gov.dwp.universal_credit.elements.child.amount",
    )
    catalog = {
        "release_version": "1.0.0",
        "programs": [
            {
                "id": "universal_credit",
                "name": "Universal Credit",
                "variable": "universal_credit",
                "parameter_prefix": "gov.dwp.universal_credit",
            },
            {
                "id": "two_child_limit_payment",
                "name": "Two Child Limit Payment",
                "variable": "two_child_limit_payment",
                "parameter_prefix": "gov.social_security_scotland.two_child_limit_payment",
            },
        ],
        "units": [
            {
                "unit_id": "parameter:gov.dwp.universal_credit.elements.child.amount",
                "kind": "parameter",
                "members": ["gov.dwp.universal_credit.elements.child.amount"],
                "source_paths": [
                    "policyengine_uk/parameters/gov/dwp/universal_credit/elements/child/amount.yaml"
                ],
                "classification": "policy_rule",
                "model_last_modified_at": "2024-01-01",
                "variable_dependencies": [],
                "parameter_references": [],
            },
            {
                "unit_id": "variable:uc_child_element",
                "kind": "variable",
                "members": ["uc_child_element"],
                "source_paths": [
                    "policyengine_uk/variables/gov/dwp/universal_credit/child_element/uc_child_element.py"
                ],
                "classification": "program_formula",
                "model_last_modified_at": "2024-01-01",
                "variable_dependencies": [],
                "parameter_references": [
                    "gov.dwp.universal_credit.elements.child.amount"
                ],
            },
            {
                "unit_id": "variable:universal_credit",
                "kind": "variable",
                "members": ["universal_credit"],
                "source_paths": [
                    "policyengine_uk/variables/gov/dwp/universal_credit/universal_credit.py"
                ],
                "classification": "program_formula",
                "model_last_modified_at": "2024-01-01",
                "variable_dependencies": ["uc_child_element"],
                "parameter_references": [],
            },
            {
                "unit_id": "variable:two_child_limit_payment",
                "kind": "variable",
                "members": ["two_child_limit_payment"],
                "source_paths": [
                    "policyengine_uk/variables/gov/social_security_scotland/two_child_limit_payment.py"
                ],
                "classification": "program_formula",
                "model_last_modified_at": "2024-01-01",
                "variable_dependencies": [],
                "parameter_references": [
                    "gov.dwp.universal_credit.elements.child.amount"
                ],
            },
        ],
    }

    context = build_program_context(
        release_root,
        catalog,
        "parameter:gov.dwp.universal_credit.elements.child.amount",
    )

    assert context["owning_program"]["program"]["id"] == "universal_credit"
    assert context["paths_to_headline_variable"] == [
        ["uc_child_element", "universal_credit"]
    ]
    assert context["external_consumers"] == [
        {
            "variable": "two_child_limit_payment",
            "program_id": "two_child_limit_payment",
            "program_name": "Two Child Limit Payment",
        }
    ]
    assert context["related_tests"] == ["policyengine_uk/tests/test_uc.py"]


def test_next_unit_orders_unchecked_by_oldest_model_change(tmp_path):
    catalog = {
        "release_version": "1.0.0",
        "units": [
            {
                "unit_id": "parameter:newer",
                "classification": "policy_rule",
                "model_last_modified_at": "2022-01-01",
            },
            {
                "unit_id": "parameter:older",
                "classification": "policy_rule",
                "model_last_modified_at": "2020-01-01",
            },
        ],
    }

    first = select_next_unit(tmp_path, catalog, create_claim=False)
    assert first["unit_id"] == "parameter:older"

    record_review(
        tmp_path,
        {
            "release_version": "1.0.0",
            "unit_id": "parameter:older",
            "audited_at": "2026-01-01",
        },
    )
    second = select_next_unit(tmp_path, catalog, create_claim=False)
    assert second["unit_id"] == "parameter:newer"


def _valid_review() -> dict:
    return {
        "release_version": "1.0.0",
        "unit_id": "parameter:gov.dwp.program.amount",
        "audited_at": "2026-10-02",
        "conclusion": "superseded_since_release",
        "summary": "The released amount omits a later statutory increase.",
        "summary_evidence_ids": ["law"],
        "periods_reviewed": ["2025-26", "2026-27"],
        "jurisdictions": ["United Kingdom"],
        "issue_title": "Update Program amount for 2026-27",
        "evidence": [
            {
                "id": "law",
                "organisation": "UK Government",
                "authority_type": "legislation",
                "title": "Example Regulations 2026, regulation 4",
                "url": "https://www.legislation.gov.uk/uksi/2026/1/regulation/4",
                "final_url": "https://www.legislation.gov.uk/uksi/2026/1/regulation/4",
                "accessed_at": "2026-10-02",
                "locator": "regulation 4",
            }
        ],
        "findings": [
            {
                "statement": "The 2026-27 amount is absent.",
                "evidence_ids": ["law"],
                "implementation_parts": [
                    {
                        "description": "Add the 2026-27 amount and effective date.",
                        "evidence_ids": ["law"],
                        "code_reference_targets": [
                            {
                                "path": "policyengine_uk/parameters/gov/dwp/program/amount.yaml",
                                "location": "values.2026-04-01.metadata.reference",
                                "evidence_ids": ["law"],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _review_catalog() -> dict:
    return {
        "release_version": "1.0.0",
        "units": [
            {
                "unit_id": "parameter:gov.dwp.program.amount",
                "model_last_modified_at": "2025-01-01",
            }
        ],
    }


def test_review_requires_code_citation_placement(tmp_path):
    release_root = tmp_path / "release"
    _write(
        release_root / "policyengine_uk/parameters/gov/dwp/program/amount.yaml",
        "values: {}\n",
    )
    review = _valid_review()
    validate_review(review, _review_catalog(), release_root)

    review["findings"][0]["implementation_parts"][0]["code_reference_targets"] = []
    with pytest.raises(ReviewValidationError, match="code_reference_targets"):
        validate_review(review, _review_catalog(), release_root)


def test_rendered_issue_uses_visible_metadata_without_hidden_marker():
    title, body = render_issue(_valid_review(), _review_catalog())

    assert title == "Update Program amount for 2026-27"
    assert "Audited release: `policyengine-uk 1.0.0`" in body
    assert "Audit unit: `parameter:gov.dwp.program.amount`" in body
    assert "legislation.gov.uk" in body
    assert "metadata.reference" in body
    assert "<!--" not in body


def test_nonissue_review_gets_a_readable_rendered_title():
    review = _valid_review()
    review["conclusion"] = "announced_not_enacted"
    review.pop("issue_title")

    title, _ = render_issue(review, _review_catalog())

    assert title == "Policy audit: parameter:gov.dwp.program.amount in 1.0.0"


def test_publish_reconciles_existing_issue_after_paginated_listing(
    tmp_path, monkeypatch
):
    review = _valid_review()
    title, body = render_issue(review, _review_catalog())
    calls: list[tuple[str, ...]] = []

    def fake_gh(*arguments, input_text=None):
        calls.append(arguments)
        if "--paginate" in arguments:
            return [
                [
                    {
                        "number": 42,
                        "title": title,
                        "body": body,
                        "html_url": "https://github.com/PolicyEngine/policyengine-uk/issues/42",
                    }
                ]
            ]
        raise AssertionError(
            "No issue should be created when an exhaustive match exists"
        )

    monkeypatch.setattr("policy_audit.github._gh", fake_gh)

    publication = publish_issue(
        "PolicyEngine/policyengine-uk",
        title,
        body,
        review,
        tmp_path,
    )

    assert publication["issue_number"] == 42
    assert publication["reconciled_existing_issue"] is True
    assert any("--paginate" in call and "--slurp" in call for call in calls)
    receipt = next(tmp_path.glob("publications/**/*.json"))
    assert json.loads(receipt.read_text())["issue_number"] == 42
