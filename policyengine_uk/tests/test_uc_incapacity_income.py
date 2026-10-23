"""Income classification, role boundaries and dated annual parameter controls."""

from pathlib import Path

import pytest
import policyengine_uk
from policyengine_core.parameters import ParameterNode
from policyengine_uk import CountryTaxBenefitSystem, Simulation


ORIGINAL = [
    "carers_allowance",
    "jsa_contrib",
    "esa_contrib",
    "maternity_allowance",
    "iidb",
    "private_pension_income",
    "state_pension",
    "uc_tariff_income",
    "spousal_maintenance_income",
    "widowed_parents_allowance",
]


def _income(parameters):
    return parameters.gov.dwp.universal_credit.means_test.income_definitions.unearned


@pytest.mark.parametrize(
    "on, included, csp",
    [
        ("2013-04-29", False, False),
        ("2014-06-15", False, False),
        ("2014-06-16", True, False),
        ("2023-11-18", True, False),
        ("2023-11-19", True, True),
    ],
)
def test_raw_statutory_income_list_boundaries(on, included, csp):
    # Raw statutory dates: this does not certify a 2014 annual UC award.
    raw = ParameterNode(
        directory_path=str(Path(policyengine_uk.__file__).parent / "parameters")
    )
    actual = list(_income(raw)(on))
    expected = ORIGINAL + (["incapacity_benefit", "sda"] if included else [])
    if csp:
        expected.append("uc_unearned_carer_support_payment")
    assert len(actual) == len(set(actual)) == len(expected)
    assert set(actual) == set(expected)
    if not included:
        assert actual == ORIGINAL


@pytest.mark.parametrize(
    "year, csp", [(2015, False), (2023, False), (2024, True), (2026, True)]
)
def test_processed_annual_list_keeps_legacy_income(year, csp):
    actual = list(_income(CountryTaxBenefitSystem().parameters)(str(year)))
    expected = ORIGINAL + ["incapacity_benefit", "sda"]
    if csp:
        expected.append("uc_unearned_carer_support_payment")
    assert len(actual) == len(set(actual)) == len(expected)
    assert set(actual) == set(expected)


@pytest.mark.parametrize(
    "reported, amount",
    [("incapacity_benefit_reported", 1000), ("sda_reported", 6206.20)],
)
def test_assessed_partner_income_counts_but_other_unit_income_does_not(
    reported, amount
):
    sim = Simulation(
        situation={
            "people": {
                "claimant": {"age": {2026: 60}},
                "partner": {"age": {2026: 58}, reported: {2026: 1000}},
                "other": {"age": {2026: 60}, reported: {2026: 2000}},
            },
            "benunits": {
                "couple": {"members": ["claimant", "partner"]},
                "other": {"members": ["other"]},
            },
            "households": {
                "household": {
                    "members": ["claimant", "partner", "other"],
                    "country": {2026: "ENGLAND"},
                }
            },
        }
    )
    assert sim.calculate("is_uc_assessed_claimant", 2026).tolist() == [True, True, True]
    assert sim.calculate("uc_unearned_income", 2026).tolist() == pytest.approx(
        [amount, amount if reported == "sda_reported" else 2000]
    )


@pytest.mark.parametrize("reported", ["incapacity_benefit_reported", "sda_reported"])
def test_same_unit_nonclaimant_report_is_excluded_input_contract(reported):
    # Not a lawful legacy award to a child: exercises the supplied-input role
    # contract without certifying legacy entitlement or child LCWRA treatment.
    sim = Simulation(
        situation={
            "people": {
                "parent": {"age": {2026: 60}},
                "child": {"age": {2026: 17}, reported: {2026: 1000}},
            },
            "benunits": {"family": {"members": ["parent", "child"]}},
            "households": {
                "household": {
                    "members": ["parent", "child"],
                    "country": {2026: "ENGLAND"},
                }
            },
        }
    )
    assert sim.calculate("is_uc_assessed_claimant", 2026).tolist() == [True, False]
    assert sim.calculate("uc_unearned_income", 2026).tolist() == [0]
