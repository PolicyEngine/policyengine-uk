"""Dataset normalisation must guard the denominator actually used."""

import pandas as pd
import pytest
from policyengine_core.simulations import Simulation as CoreSimulation

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKSingleYearDataset


YEAR = 2025
# Synthetic totals make the existing allocation rules independently checkable:
# corporate incidence is £150 times shareholding; consumer revenue is £7,000.
REFORM = {
    "household.wealth.national_balance_sheet.household.financial_net_worth": {
        YEAR: 1_000_000,
    },
    "gov.hmrc.business_rates.statistics.revenue.ENGLAND": {YEAR: 100},
    "gov.hmrc.business_rates.statistics.revenue.ENGLAND_CENTRAL_LIST": {YEAR: 0},
    "gov.hmrc.business_rates.statistics.revenue.SCOTLAND": {YEAR: 0},
    "gov.hmrc.business_rates.statistics.revenue.WALES": {YEAR: 0},
    "gov.hmrc.business_rates.statistics.revenue.WALES_CENTRAL_LIST": {YEAR: 0},
    "gov.hmrc.business_rates.statistics.revenue.NORTHERN_IRELAND": {YEAR: 0},
    "gov.hmrc.stamp_duty.statistics.residential.corporate.revenue": {YEAR: 20},
    "gov.hmrc.stamp_duty.statistics.non_residential.corporate.revenue": {YEAR: 30},
    # No household buys property, so expected_sdlt is zero and household_tax
    # holds corporate SDLT once, through corporate_sdlt. Abolishing SDLT would
    # zero corporate SDLT too (#2159).
    "gov.contrib.policyengine.budget.consumer_incident_tax_change": {YEAR: 0.000007},
}


def incidence_simulation(weights, wealth, consumption, *, dataset=True):
    households = {
        "household_id": [1, 2],
        "household_weight": weights,
        "region": ["LONDON", "WALES"],
        "council_tax": [0, 0],
        "rent": [0, 0],
        "tenure_type": ["OWNED_OUTRIGHT", "OWNED_OUTRIGHT"],
        "household_owns_tv": [False, False],
        "corporate_wealth": wealth,
        "food_and_non_alcoholic_beverages_consumption": consumption,
    }
    if dataset:
        return Simulation(
            dataset=UKSingleYearDataset(
                person=pd.DataFrame(
                    {
                        "person_id": [1, 2],
                        "person_benunit_id": [1, 2],
                        "person_household_id": [1, 2],
                        "age": [40, 50],
                    }
                ),
                benunit=pd.DataFrame({"benunit_id": [1, 2]}),
                household=pd.DataFrame(households),
                fiscal_year=YEAR,
            ),
            reform=REFORM,
        )

    # The UK situation adapter materialises a dataset too. Build directly through
    # Core to retain the genuinely dataset-free path of these formulas.
    simulation = CoreSimulation(
        tax_benefit_system=CountryTaxBenefitSystem(),
        situation={
            "people": {
                f"person_{i}": {"age": {YEAR: age}} for i, age in enumerate([40, 50])
            },
            "benunits": {
                f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(2)
            },
            "households": {
                f"household_{i}": {
                    "members": [f"person_{i}"],
                    **{
                        name: {YEAR: values[i]}
                        for name, values in households.items()
                        if name != "household_id"
                    },
                }
                for i in range(2)
            },
        },
        reform=REFORM,
    )
    assert simulation.dataset is None
    return simulation


@pytest.mark.parametrize(
    "variable, expected",
    [
        ("shareholding", [0.01, 0]),
        ("consumption_shareholding", [0, 0]),
        # The fallback allocates £7,000 over existing aggregate consumption £846bn.
        ("consumer_incident_tax_revenue_change", [21 / 846_000, 0]),
        ("corporate_tax_incidence", [1.5, 0]),
        ("household_tax", [1.5 + 21 / 846_000, 0]),
    ],
)
def test_zero_weight_holder_uses_existing_fallback(variable, expected):
    sim = incidence_simulation([0, 1], [10_000, 0], [3_000, 0])

    assert sim.calculate(variable, YEAR) == pytest.approx(expected)


@pytest.mark.parametrize(
    "variable, expected",
    [
        ("shareholding", [0.2, 0.6]),
        ("consumption_shareholding", [3 / 7, 1 / 7]),
        ("consumer_incident_tax_revenue_change", [3_000, 1_000]),
        ("corporate_tax_incidence", [30, 90]),
        ("household_tax", [3_030, 1_090]),
    ],
)
def test_positive_weighted_totals_keep_dataset_normalisation(variable, expected):
    sim = incidence_simulation([2, 1], [10_000, 30_000], [3_000, 1_000])

    assert sim.calculate(variable, YEAR) == pytest.approx(expected)


@pytest.mark.parametrize(
    "variable",
    [
        "shareholding",
        "consumption_shareholding",
        "consumer_incident_tax_revenue_change",
        "corporate_tax_incidence",
        "household_tax",
    ],
)
def test_zero_values_keep_zero_fallback(variable):
    sim = incidence_simulation([2, 1], [0, 0], [0, 0])

    assert sim.calculate(variable, YEAR) == pytest.approx([0, 0])


@pytest.mark.parametrize(
    "variable, expected",
    [
        ("shareholding", [0.01, 0.03]),
        ("consumption_shareholding", [0, 0]),
        ("consumer_incident_tax_revenue_change", [21 / 846_000, 7 / 846_000]),
        ("corporate_tax_incidence", [1.5, 4.5]),
    ],
)
def test_situation_keeps_no_dataset_fallback(variable, expected):
    sim = incidence_simulation([2, 1], [10_000, 30_000], [3_000, 1_000], dataset=False)

    assert sim.calculate(variable, YEAR) == pytest.approx(expected)
