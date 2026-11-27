"""Reform-to-incidence tests for the firm rules added in the fourth audit.

Each test reforms one parameter of a new rule and checks that the weighted
change reaches ``firm_tax_change_total`` and that household
``firm_tax_incidence`` sums (weighted) to it, or, for rules whose rates reach
households elsewhere, that it does not.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset

YEAR = 2026
HOUSEHOLD_WEIGHTS = [100.0, 200.0]
FIRM_WEIGHTS = [5.0, 7.0, 11.0]
ALWAYS = "2020-01-01.2035-12-31"


def dataset(**firm_columns) -> UKSingleYearDataset:
    firm = {
        "firm_id": [1, 2, 3],
        "firm_weight": FIRM_WEIGHTS,
        "firm_taxable_trading_profit": [1_000_000.0, 100_000.0, 40_000.0],
        "firm_paybill": [2_000_000.0, 300_000.0, 0.0],
        "firm_employees": [40.0, 8.0, 0.0],
    }
    firm.update(firm_columns)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 2],
                "age": [30, 50],
                "employment_income": [20_000.0, 60_000.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "household_weight": HOUSEHOLD_WEIGHTS,
                "region": "LONDON",
                "rent": 0.0,
                "tenure_type": "OWNED_OUTRIGHT",
                "council_tax": 0.0,
                "corporate_sector_wealth": [100_000.0, 200_000.0],
            }
        ),
        firm=pd.DataFrame(firm),
        fiscal_year=YEAR,
    )


def change_total_and_incidence(data, reform):
    simulation = Microsimulation(dataset=data, reform=reform)
    total = np.asarray(simulation.calculate("firm_tax_change_total", YEAR))
    incidence = np.asarray(simulation.calculate("firm_tax_incidence", YEAR))
    return simulation, total, (incidence * HOUSEHOLD_WEIGHTS).sum()


def test_soft_drinks_levy_rate_reform_reaches_firm_incidence():
    # 2026-27 higher rate 27.8p. Firm 1 has 2m litres, firm 2 500,000 (a
    # small producer), firm 3 none. At 30p: 2,000,000 x 0.022 = 44,000 for
    # firm 1 only; 5 x 44,000 = 220,000.
    data = dataset(firm_sdil_litres_higher_rate=[2_000_000.0, 500_000.0, 0.0])
    _, total, incidence = change_total_and_incidence(
        data,
        {"gov.hmrc.soft_drinks_industry_levy.rate.higher": {ALWAYS: 0.30}},
    )
    assert total == pytest.approx([220_000, 220_000], abs=1)
    assert incidence == pytest.approx(220_000, abs=1)


def test_plastic_packaging_tax_rate_reform_reaches_firm_incidence():
    # 2026-27 rate 228.82. Firm 1 100 tonnes, firm 2 8 tonnes (under the
    # registration threshold), firm 3 20 tonnes. At 300: (300 - 228.82) x
    # 100 = 7,118 and x 20 = 1,423.6; 5 x 7,118 + 11 x 1,423.6 = 51,249.6.
    data = dataset(firm_plastic_packaging_tonnes_chargeable=[100.0, 8.0, 20.0])
    _, total, incidence = change_total_and_incidence(
        data, {"gov.hmrc.plastic_packaging_tax.rate": {ALWAYS: 300}}
    )
    assert total == pytest.approx([51_249.6, 51_249.6], abs=1)
    assert incidence == pytest.approx(51_249.6, abs=1)


def test_partial_exemption_de_minimis_limit_reaches_firm_incidence():
    # Firm 2: 150,000 standard-rated and 50,000 exempt supplies, 30,000 of
    # input VAT, de minimis applied: exempt input tax 7,500 is within the
    # 7,500 limit, so it recovers all 30,000. With the limits at 0 both
    # tests fail and it recovers 75%: VAT rises by 7,500; 7 x 7,500 = 52,500.
    data = dataset(
        firm_standard_rated_supplies=[0.0, 150_000.0, 0.0],
        firm_exempt_supplies=[0.0, 50_000.0, 0.0],
        firm_input_vat=[0.0, 30_000.0, 0.0],
        firm_applies_partial_exemption_de_minimis=[False, True, False],
    )
    simulation, total, incidence = change_total_and_incidence(
        data,
        {
            "gov.hmrc.vat.partial_exemption.de_minimis.monthly_limit": {ALWAYS: 0},
            "gov.hmrc.vat.partial_exemption.de_minimis.simplified.monthly_limit": {
                ALWAYS: 0
            },
        },
    )
    baseline_vat = np.asarray(simulation.baseline.calculate("firm_vat", YEAR))
    assert baseline_vat[1] == pytest.approx(0, abs=0.01)
    assert total == pytest.approx([52_500, 52_500], abs=1)
    assert incidence == pytest.approx(52_500, abs=1)


def test_secondary_rate_reform_reaches_class_1b_and_termination_class_1a():
    # Firm 1: PSA earnings 60,000 and tax 40,000; termination awards 130,000
    # for one employee. Raising the secondary rate from 15% to 16% adds 1% x
    # 100,000 = 1,000 of Class 1B and 1% x 100,000 = 1,000 of termination
    # Class 1A, both firm-only: 5 x 2,000 = 10,000. Firm 1's own employer NIC
    # also rises, but that reaches households through ni_employer, and the
    # change in its Employment Allowance is 0 (it stays at 10,500).
    data = dataset(
        firm_psa_chargeable_earnings=[60_000.0, 0.0, 0.0],
        firm_psa_income_tax=[40_000.0, 0.0, 0.0],
        firm_termination_awards=[130_000.0, 0.0, 0.0],
        firm_termination_award_recipients=[1, 0, 0],
    )
    simulation, total, incidence = change_total_and_incidence(
        data,
        {
            "gov.hmrc.national_insurance.class_1.employer_scale[1].rate": {
                ALWAYS: 0.16
            },
        },
    )
    change = np.asarray(simulation.calculate("firm_class_1b_ni", YEAR)) - np.asarray(
        simulation.baseline.calculate("firm_class_1b_ni", YEAR)
    )
    assert change == pytest.approx([1_000, 0, 0], abs=0.5)
    # Firm 2's allowance: (300,000 - 8 x 5,000) x 15% = 39,000 > 10,500, so
    # it is unchanged too.
    assert total == pytest.approx([10_000, 10_000], abs=5)
    assert incidence == pytest.approx(10_000, abs=5)


def test_levy_rate_reform_reaches_incidence_through_off_payroll_payments():
    # Firm 2: paybill 300,000 plus 3,000,000 of deemed payments. Levy at 0.5%:
    # 16,500 - 15,000 = 1,500; at 1%: 33,000 - 15,000 = 18,000. Firm 1:
    # 10,000 under the allowance, then 20,000 - 15,000 = 5,000.
    # 5 x 5,000 + 7 x 16,500 = 140,500.
    data = dataset(firm_off_payroll_deemed_payments=[0.0, 3_000_000.0, 0.0])
    _, total, incidence = change_total_and_incidence(
        data, {"gov.hmrc.apprenticeship_levy.rate": {ALWAYS: 0.01}}
    )
    assert total == pytest.approx([140_500, 140_500], abs=1)
    assert incidence == pytest.approx(140_500, abs=1)


def test_off_payroll_ni_is_not_firm_only():
    # A rise in the secondary rate changes firm 2's off-payroll NIC but not
    # firm_only_tax, since the rate reaches households through ni_employer.
    data = dataset(
        firm_off_payroll_deemed_payments=[0.0, 100_000.0, 0.0],
        firm_off_payroll_deemed_workers=[0, 2, 0],
    )
    simulation = Microsimulation(
        dataset=data,
        reform={
            "gov.hmrc.national_insurance.class_1.employer_scale[1].rate": {ALWAYS: 0.16}
        },
    )
    off_payroll = np.asarray(simulation.calculate("firm_off_payroll_employer_ni", YEAR))
    assert off_payroll[1] == pytest.approx(0.16 * 90_000, abs=0.5)
    only = np.asarray(simulation.calculate("firm_only_tax", YEAR)) - np.asarray(
        simulation.baseline.calculate("firm_only_tax", YEAR)
    )
    assert only == pytest.approx([0, 0, 0], abs=0.01)


def test_group_relief_changes_a_main_rate_reform_total():
    # Firm 1 claims 600,000 of group relief, leaving 400,000 of profit. A
    # main rate rise from 25% to 26% then adds 1% x 400,000 = 4,000 for firm
    # 1 and 1% x 100,000 = 1,000 for firm 2: 5 x 4,000 + 7 x 1,000 = 27,000.
    data = dataset(firm_group_relief_claimed=[600_000.0, 0.0, 0.0])
    _, total, incidence = change_total_and_incidence(
        data, {"gov.hmrc.corporation_tax.main_rate": {ALWAYS: 0.26}}
    )
    assert total == pytest.approx([27_000, 27_000], abs=1)
    assert incidence == pytest.approx(27_000, abs=1)


def test_northern_ireland_regional_rate_reform_reaches_firm_incidence():
    # Firm 3 is in Belfast with a net annual value of 30,000; 2026-27
    # regional rate 0.3079. At 0.40: 30,000 x 0.0921 = 2,763; 11 x 2,763 =
    # 30,393. Firms 1 and 2 are in London with no rateable value.
    data = dataset(
        firm_region=["LONDON", "LONDON", "NORTHERN_IRELAND"],
        firm_northern_ireland_district=["UNKNOWN", "UNKNOWN", "BELFAST"],
        firm_rateable_value=[0.0, 0.0, 30_000.0],
    )
    simulation, total, incidence = change_total_and_incidence(
        data,
        {"gov.hmrc.business_rates.northern_ireland.regional_rate": {ALWAYS: 0.40}},
    )
    baseline = np.asarray(simulation.baseline.calculate("firm_business_rates", YEAR))
    assert baseline == pytest.approx([0, 0, 19_508.64], abs=0.1)
    assert total == pytest.approx([30_393, 30_393], abs=1)
    assert incidence == pytest.approx(30_393, abs=1)


def test_patent_box_special_rate_reform_reaches_firm_incidence():
    # Firm 1: profit 1,000,000 with 400,000 of relevant IP profits, 2026-27.
    # Baseline deduction 400,000 x 15/25 = 240,000. With a 15% special rate:
    # 400,000 x 10/25 = 160,000, so 80,000 more profit at 25% = 20,000;
    # 5 x 20,000 = 100,000.
    data = dataset(firm_relevant_ip_profits=[400_000.0, 0.0, 0.0])
    _, total, incidence = change_total_and_incidence(
        data, {"gov.hmrc.corporation_tax.patent_box.special_ip_rate": {ALWAYS: 0.15}}
    )
    assert total == pytest.approx([100_000, 100_000], abs=1)
    assert incidence == pytest.approx(100_000, abs=1)


@pytest.mark.parametrize(
    "column, values, parameter, value, expected",
    [
        # Firm 1: 100m of RPD profits. 5% instead of 4% on 75m: 750,000; x 5.
        (
            "firm_rpd_profits",
            [100_000_000.0, 0.0, 0.0],
            "gov.hmrc.residential_property_developer_tax.rate",
            0.05,
            3_750_000,
        ),
        # Firm 2: 100m of UK digital services revenues in a group with 600m
        # worldwide (supplied below). 3% instead of 2% on 75m: 750,000; x 7.
        (
            "firm_uk_digital_services_revenues",
            [0.0, 100_000_000.0, 0.0],
            "gov.hmrc.digital_services_tax.rate",
            0.03,
            5_250_000,
        ),
        # Firm 3: 1m of levy profits. 40% instead of 38%: 20,000; x 11.
        (
            "firm_epl_profits",
            [0.0, 0.0, 1_000_000.0],
            "gov.hmrc.energy_profits_levy.rate",
            0.40,
            220_000,
        ),
    ],
    ids=["rpdt", "dst", "epl"],
)
def test_profit_tax_rate_reforms_reach_firm_incidence(
    column, values, parameter, value, expected
):
    data = dataset(
        **{column: values},
        firm_group_digital_services_revenues=[0.0, 600_000_000.0, 0.0],
    )
    _, total, incidence = change_total_and_incidence(data, {parameter: {ALWAYS: value}})
    assert total == pytest.approx([expected, expected], abs=1)
    assert incidence == pytest.approx(expected, abs=1)
