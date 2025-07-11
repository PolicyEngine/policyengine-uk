BASIC_RATE_REFORM = {
    "gov.hmrc.income_tax.rates.uk[0].rate": 0.21,
}

HIGHER_RATE_REFORM = {
    "gov.hmrc.income_tax.rates.uk[1].rate": 0.42,
}

PERSONAL_ALLOWANCE_REFORM = {
    "gov.hmrc.income_tax.allowances.personal_allowance.amount": 13000,
}

CHILD_BENEFIT_REFORM = {
    "gov.hmrc.child_benefit.amount.additional": 25,
}

UC_PHASE_OUT_REFORM = {
    "gov.dwp.universal_credit.means_test.reduction_rate": 0.2,
}

NATIONAL_INSURANCE_REFORM = {
    "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.10,
}

VAT_REFORM = {
    "gov.hmrc.vat.standard_rate": 0.22,
}

ADDITIONAL_RATE_REFORM = {
    "gov.hmrc.income_tax.rates.uk[2].rate": 0.48,
}

import pytest
from policyengine_uk import Microsimulation

baseline = Microsimulation()


def get_fiscal_impact(reform: dict):
    baseline_revenue = baseline.calculate("gov_balance", 2029).sum()
    reform_simulation = Microsimulation(reform=reform)
    reform_revenue = reform_simulation.calculate("gov_balance", 2029).sum()
    return (reform_revenue - baseline_revenue) / 1e9


reform_names = [
    "Raise basic rate by 1pp",
    "Raise higher rate by 1pp",
    "Raise personal allowance by ~800GBP/year",
    "Raise child benefit by 25GBP/week per additional child",
    "Reduce Universal Credit taper rate to 20%",
    "Raise Class 1 main employee NICs rate to 10%",
    "Raise VAT standard rate by 2pp",
    "Raise additional rate by 3pp",
]

expected_revenues = [
    7.8,
    5.0,
    0.8,
    -1.3,
    -38.2,
    12.4,
    19.5,
    4.5,
]

reforms = [
    BASIC_RATE_REFORM,
    HIGHER_RATE_REFORM,
    PERSONAL_ALLOWANCE_REFORM,
    CHILD_BENEFIT_REFORM,
    UC_PHASE_OUT_REFORM,
    NATIONAL_INSURANCE_REFORM,
    VAT_REFORM,
    ADDITIONAL_RATE_REFORM,
]


@pytest.mark.parametrize(
    "reform, reform_name, expected_impact",
    zip(
        reforms,
        reform_names,
        expected_revenues,
    ),
    ids=reform_names,
)
def test_reform_fiscal_impacts(reform, reform_name, expected_impact):
    impact = get_fiscal_impact(reform)
    assert (
        abs(impact - expected_impact) < 0.1
    ), f"Impact for {reform_name} is {impact:.1f} billion, expected {expected_impact:.1f} billion"
