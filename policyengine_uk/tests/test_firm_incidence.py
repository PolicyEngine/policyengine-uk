"""Firm tax aggregates and their household incidence.

``firm_tax`` and ``firm_only_tax`` are firm liabilities. ``firm_tax_change_total``
is the firm_weight-weighted change in ``firm_only_tax`` between a reform and
its baseline, and ``firm_tax_incidence`` spreads it over households. Both are
0 in a household situation and without a baseline, and are not yet terms of
any household tax.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKSingleYearDataset

YEAR = 2026
# Raise the corporation tax main rate from 25% to 30%.
CT_REFORM = {"gov.hmrc.corporation_tax.main_rate": {"2020-01-01.2035-12-31": 0.3}}

# 2026-27 values: employer Class 1 15% above 96.153846 a week x 52 (about
# 5,000 a year per employee); Employment Allowance 10,500; corporation tax 25%
# main and 19% small profits, marginal relief 3/200 between 50,000 and 250,000;
# business rates 43.2p small and 48p standard multipliers, small business rate
# relief in full up to a rateable value of 12,000; VAT 20%, registration above
# 90,000 of taxable turnover.
FIRMS = {
    # A single-director company: no Employment Allowance.
    "consultancy": {
        "firm_is_single_director_company": True,
        "firm_employees": 1,
        "firm_paybill": 60_000,
        "firm_taxable_trading_profit": 45_000,
    },
    # A sole trader: no corporation tax, and under the VAT threshold.
    "shop": {
        "firm_legal_form": "SOLE_TRADER",
        "firm_employees": 2,
        "firm_paybill": 50_000,
        "firm_taxable_trading_profit": 70_000,
        "firm_rateable_value": 10_000,
        "firm_standard_rated_supplies": 85_000,
    },
    # A company with exempt distributions, which raise its augmented profits
    # and so cut its marginal relief.
    "manufacturer": {
        "firm_employees": 10,
        "firm_paybill": 400_000,
        "firm_taxable_trading_profit": 100_000,
        "firm_exempt_distributions": 100_000,
        "firm_rateable_value": 60_000,
        "firm_standard_rated_supplies": 500_000,
        "firm_input_vat": 40_000,
    },
}

EXPECTED = {
    # Consultancy: 19% x 45,000 = 8,550 (augmented profits under 50,000).
    # Shop: a sole trader pays none.
    # Manufacturer: augmented 100,000 + 100,000 = 200,000, in the band;
    # relief 3/200 x (250,000 - 200,000) x 100,000/200,000 = 375;
    # 25% x 100,000 - 375 = 24,625.
    "corporation_tax": [8_550, 0, 24_625],
    # Consultancy: excluded as a single-director company.
    # Shop: min(10,500, (50,000 - 2 x 5,000) x 15% = 6,000) = 6,000.
    # Manufacturer: min(10,500, (400,000 - 10 x 5,000) x 15% = 52,500).
    "employment_allowance": [0, 6_000, 10_500],
    # (60,000 - 5,000) x 15% = 8,250; 6,000 - 6,000 = 0; 52,500 - 10,500.
    "firm_employer_ni": [8_250, 0, 42_000],
    # 0.5% of each paybill is under the 15,000 allowance.
    "apprenticeship_levy": [0, 0, 0],
    # Consultancy: no property. Shop: 10,000 x 43.2p = 4,320, all relieved by
    # small business rate relief. Manufacturer: 60,000 x 48p = 28,800.
    "firm_business_rates": [0, 0, 28_800],
    # Shop: 85,000 is under the threshold. Manufacturer: 20% x 500,000
    # - 40,000 = 60,000.
    "firm_vat": [0, 0, 60_000],
    # Sums of the above (bank surcharge 0):
    # 8,550 + 8,250 = 16,800; 0; 24,625 + 42,000 + 28,800 + 60,000 = 155,425.
    "firm_tax": [16_800, 0, 155_425],
    # Corporation tax + apprenticeship levy + business rates (the Employment
    # Allowance moves with employer NI and is left out): 8,550; 0;
    # 24,625 + 28,800 = 53,425.
    "firm_only_tax": [8_550, 0, 53_425],
}

HOUSEHOLD = {
    "people": {"adult": {"age": 40, "employment_income": 40_000}},
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"], "corporate_sector_wealth": 1e6}},
}


@pytest.fixture(scope="module")
def firms_only():
    return Simulation(situation={"firms": FIRMS})


@pytest.mark.parametrize("variable", sorted(EXPECTED))
def test_firms_only_situation_hand_computed(firms_only, variable):
    assert firms_only.populations["person"].count == 0
    assert firms_only.calculate(variable, YEAR) == pytest.approx(
        EXPECTED[variable], abs=1
    )


@pytest.mark.parametrize(
    "situation",
    [HOUSEHOLD, {**HOUSEHOLD, "firms": FIRMS}],
    ids=["household", "household_and_firms"],
)
@pytest.mark.parametrize("reform", [None, CT_REFORM], ids=["no_reform", "reform"])
def test_incidence_is_zero_in_a_situation(situation, reform):
    """A situation is not data, so even with firms and a reform that changes
    their liability the aggregate and its incidence are 0. (Without a reform
    the UK simulation's baseline is a clone of itself.)"""
    simulation = Simulation(situation=situation, reform=reform)
    assert simulation.calculate("firm_tax_change_total", YEAR).tolist() == [0]
    assert simulation.calculate("firm_tax_incidence", YEAR).tolist() == [0]


def test_a_situation_reform_still_changes_firm_liability():
    """The zero above is not because the reform misses firms."""
    simulation = Simulation(situation={**HOUSEHOLD, "firms": FIRMS}, reform=CT_REFORM)
    change = simulation.calculate(
        "corporation_tax", YEAR
    ) - simulation.baseline.calculate("corporation_tax", YEAR)
    # Only the manufacturer, in the marginal relief band, pays the main rate:
    # 5% x 100,000 = 5,000 more; marginal relief does not depend on it.
    assert change == pytest.approx([0, 0, 5_000], abs=0.01)


HOUSEHOLD_WEIGHTS = [100.0, 200.0]
FIRM_WEIGHTS = [5.0, 7.0, 11.0]
# Firm profits: above the upper limit, in the marginal relief band, and under
# the lower limit.
FIRM_PROFITS = [1_000_000.0, 100_000.0, 40_000.0]


def dataset(year: int = YEAR) -> UKSingleYearDataset:
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
                # Weighted total 100 x 100,000 + 200 x 200,000 = 50,000,000,
                # so shareholdings are 0.002 and 0.004 and sum (weighted) to 1.
                "corporate_sector_wealth": [100_000.0, 200_000.0],
            }
        ),
        firm=pd.DataFrame(
            {
                "firm_id": [1, 2, 3],
                "firm_weight": FIRM_WEIGHTS,
                "firm_taxable_trading_profit": FIRM_PROFITS,
                "firm_paybill": [2_000_000.0, 300_000.0, 0.0],
                "firm_employees": [40.0, 8.0, 0.0],
                "firm_rateable_value": [150_000.0, 20_000.0, 0.0],
            }
        ),
        fiscal_year=year,
    )


@pytest.fixture(scope="module")
def reformed():
    return Microsimulation(dataset=dataset(), reform=CT_REFORM)


def test_dataset_change_total_is_the_weighted_firm_only_tax_change(reformed):
    # Per firm, the 5-point rise in the main rate adds 5% x 1,000,000 =
    # 50,000; 5% x 100,000 = 5,000 (marginal relief unchanged); and 0 under
    # the small profits rate. Nothing else in firm_only_tax moves.
    per_firm = np.asarray(reformed.calculate("firm_only_tax", YEAR)) - np.asarray(
        reformed.baseline.calculate("firm_only_tax", YEAR)
    )
    assert per_firm == pytest.approx([50_000, 5_000, 0], abs=0.01)
    # Weighted: 5 x 50,000 + 7 x 5,000 + 11 x 0 = 285,000.
    total = np.asarray(reformed.calculate("firm_tax_change_total", YEAR))
    assert total == pytest.approx([285_000, 285_000], abs=0.01)


def test_dataset_incidence_sums_to_the_change_total(reformed):
    shareholding = np.asarray(reformed.calculate("shareholding", YEAR))
    assert shareholding == pytest.approx([0.002, 0.004])
    incidence = np.asarray(reformed.calculate("firm_tax_incidence", YEAR))
    # Capital incidence 1: 285,000 x 0.002 = 570 and 285,000 x 0.004 = 1,140.
    assert incidence == pytest.approx([570, 1_140])
    # 100 x 570 + 200 x 1,140 = 285,000.
    assert (incidence * HOUSEHOLD_WEIGHTS).sum() == pytest.approx(285_000)


def test_dataset_labour_incidence_sums_to_the_change_total():
    """With all of the change on workers, each household bears its share of
    weighted employment income: 100 x 20,000 + 200 x 60,000 = 14,000,000, so
    shares of 1/700 and 3/700 of 285,000."""
    simulation = Microsimulation(
        dataset=dataset(),
        reform={
            **CT_REFORM,
            "gov.contrib.policyengine.firm_incidence.capital": {
                "2020-01-01.2035-12-31": 0
            },
            "gov.contrib.policyengine.firm_incidence.labour": {
                "2020-01-01.2035-12-31": 1
            },
        },
    )
    incidence = np.asarray(simulation.calculate("firm_tax_incidence", YEAR))
    assert incidence == pytest.approx([285_000 / 700, 3 * 285_000 / 700])
    assert (incidence * HOUSEHOLD_WEIGHTS).sum() == pytest.approx(285_000)


def test_dataset_without_a_reform_has_no_change():
    """A UK simulation built without a reform has a clone of itself as its
    baseline, so the change is 0."""
    simulation = Microsimulation(dataset=dataset())
    for variable in ("firm_tax_change_total", "firm_tax_incidence"):
        assert np.asarray(simulation.calculate(variable, YEAR)).tolist() == [0, 0]


def test_dataset_with_no_baseline_has_no_change():
    """A UK simulation always has a baseline (its baseline's is a clone of
    it), so take it away to reach the no-baseline branch: the change is 0,
    though the firms are taxed."""
    simulation = Microsimulation(dataset=dataset(), reform=CT_REFORM)
    simulation.baseline = None
    assert np.asarray(simulation.calculate("firm_only_tax", YEAR)).sum() > 0
    for variable in ("firm_tax_change_total", "firm_tax_incidence"):
        assert np.asarray(simulation.calculate(variable, YEAR)).tolist() == [0, 0]


def test_dataset_incidence_leaves_household_tax_unchanged(reformed):
    """Not yet wired in: a corporation tax reform leaves household_tax alone."""
    assert np.array_equal(
        np.asarray(reformed.calculate("household_tax", YEAR)),
        np.asarray(reformed.baseline.calculate("household_tax", YEAR)),
    )


def small_payroll_dataset() -> UKSingleYearDataset:
    """The dataset above with the second firm's employer NI under the
    Employment Allowance: (60,000 - 8 x 5,000) x 15% = 3,000."""
    data = dataset()
    data.firm.loc[1, "firm_paybill"] = 60_000.0
    return data


EMPLOYER_NI_REFORM = {
    "gov.hmrc.national_insurance.class_1.employer_scale[1].rate": {
        "2020-01-01.2035-12-31": 0.2
    }
}


def test_employer_ni_rate_reform_does_not_reach_firm_incidence():
    """Employer NI rates reach households through ni_employer, so the larger
    Employment Allowance a rate rise brings a firm under the cap (3,000 to
    4,000 for the second firm) must not count as a firm-only tax change."""
    simulation = Microsimulation(
        dataset=small_payroll_dataset(), reform=EMPLOYER_NI_REFORM
    )
    allowance_change = np.asarray(
        simulation.calculate("employment_allowance", YEAR)
    ) - np.asarray(simulation.baseline.calculate("employment_allowance", YEAR))
    assert allowance_change == pytest.approx([0, 1_000, 0], abs=0.01)
    for variable in ("firm_tax_change_total", "firm_tax_incidence"):
        assert np.asarray(simulation.calculate(variable, YEAR)) == pytest.approx(
            [0, 0], abs=0.01
        )


def test_employment_allowance_reform_reaches_firm_incidence():
    """Cutting the allowance to 5,000 at baseline liabilities: the first firm
    (liability 270,000) loses 5,500, the second (liability 3,000) keeps
    3,000, the third has none. Weighted: 5 x 5,500 = 27,500 more tax."""
    simulation = Microsimulation(
        dataset=small_payroll_dataset(),
        reform={
            "gov.hmrc.national_insurance.employment_allowance.amount": {
                "2020-01-01.2035-12-31": 5_000
            }
        },
    )
    total = np.asarray(simulation.calculate("firm_tax_change_total", YEAR))
    assert total == pytest.approx([27_500, 27_500], abs=0.01)


def test_employer_ni_rate_reform_does_not_flip_prior_year_eligibility():
    """In 2024-25 a firm whose prior-year secondary liabilities reach
    100,000 loses the allowance. A rate rise that lifts a firm from 90,000
    to about 130,000 of liabilities would take its 5,000 allowance away;
    that is an employer NI change, reaching households through ni_employer,
    so the firm-only total holds last year's liabilities at baseline and
    does not move. 2024-25: 13.8% above 9,100 a year; one employee paid
    9,100 + 90,000 / 0.138 = 661,275 (about 90,000 of liabilities)."""
    data = dataset(2024)
    data.firm = data.firm.iloc[:1].copy()
    data.firm["firm_paybill"] = 9_100 + 90_000 / 0.138
    data.firm["firm_employees"] = 1.0
    data.firm["firm_taxable_trading_profit"] = 0.0
    data.firm["firm_rateable_value"] = 0.0
    simulation = Microsimulation(dataset=data, reform=EMPLOYER_NI_REFORM)
    baseline_eligible = simulation.baseline.calculate(
        "employment_allowance_eligible", 2024
    )
    reform_eligible = simulation.calculate("employment_allowance_eligible", 2024)
    # The flip the total must not count.
    assert np.asarray(baseline_eligible).tolist() == [True]
    assert np.asarray(reform_eligible).tolist() == [False]
    total = np.asarray(simulation.calculate("firm_tax_change_total", 2024))
    assert total == pytest.approx([0, 0], abs=0.01)


def test_dataset_with_a_firmless_baseline_raises():
    """The baseline must carry the same firm table; one built without firms
    cannot be compared firm by firm."""
    data = dataset()
    firmless = UKSingleYearDataset(
        person=data.person,
        benunit=data.benunit,
        household=data.household,
        fiscal_year=YEAR,
    )
    simulation = Microsimulation(dataset=dataset(), reform=CT_REFORM)
    simulation.baseline = Microsimulation(dataset=firmless)
    with pytest.raises(ValueError, match="different number of firms"):
        simulation.calculate("firm_tax_change_total", YEAR)


@pytest.mark.parametrize("year", [2025, 2024])
def test_employment_allowance_under_rules_matches_the_variables(year):
    """With no reform, the firm-only total's copy of the Employment Allowance
    rules gives the same weighted allowance as employment_allowance."""
    from policyengine_uk.variables.contrib.policyengine.firm.firm_tax_change_total import (
        _employment_allowance_under_rules,
    )

    data = dataset(year)
    # A charity public body (eligible), a non-charity public body (excluded),
    # a single-director company (excluded), a non-claimant group member
    # (excluded), and two ordinary firms with prior-year liabilities over and
    # under 100,000 (the over one excluded in 2024-25 only).
    data.firm = pd.DataFrame(
        {
            "firm_id": [1, 2, 3, 4, 5, 6],
            "firm_weight": [2.0, 3.0, 5.0, 7.0, 11.0, 13.0],
            "firm_paybill": [300_000.0] * 6,
            "firm_employees": [8.0] * 6,
            "firm_is_public_body": [True, True, False, False, False, False],
            "firm_is_charity": [True, False, False, False, False, False],
            "firm_is_single_director_company": [False, False, True] + [False] * 3,
            "firm_claims_employment_allowance": [True] * 3 + [False] + [True] * 2,
            "firm_prior_year_secondary_class_1_liabilities": [
                0.0,
                0.0,
                0.0,
                0.0,
                150_000.0,
                50_000.0,
            ],
        }
    )
    simulation = Microsimulation(dataset=data)
    firms = simulation.populations["firm"]
    liability = firms("firm_employer_ni_before_allowance", year)
    expected = (
        np.asarray(simulation.calculate("employment_allowance", year))
        * np.asarray(firms("firm_weight", year))
    ).sum()
    actual = _employment_allowance_under_rules(simulation, year, firms, liability)
    assert actual == pytest.approx(expected)
    eligible = np.asarray(simulation.calculate("employment_allowance_eligible", year))
    if year == 2024:
        assert eligible.tolist() == [True, False, False, False, False, True]
    else:
        assert eligible.tolist() == [True, False, False, False, True, True]
