"""Firm taxes in a Microsimulation over a seeded synthetic firm table.

About 200 synthetic firms, with a mix of legal forms, losses, capital
spending, property and VAT, sit beside a few households. Each firm tax is
checked, summed with firm_weight, against an independent numpy calculation
on the firms where the rule is unambiguous, using 2026-27 parameter values
read from the system. The checks also cover the firm_tax identity, finite
values for every firm variable, and that adding the firm table leaves the
household aggregates unchanged. All totals are toy numbers from synthetic
data, not estimates.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation
from policyengine_uk.data import UKSingleYearDataset

YEAR = 2026
N_FIRMS = 200
SEED = 20260401
# Firm variables are stored as float32.
TOL = 1e-5


def firm_table() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n = N_FIRMS
    legal_form = rng.choice(
        ["COMPANY", "SOLE_TRADER", "PARTNERSHIP", "OTHER"],
        size=n,
        p=[0.6, 0.2, 0.15, 0.05],
    )
    employees = rng.integers(0, 120, size=n).astype(float)
    # Average pay from 3,000 (below the secondary threshold) to 80,000.
    paybill = employees * rng.uniform(3_000, 80_000, size=n)
    # About a quarter of firms make a loss.
    profit = rng.uniform(-200_000, 1_500_000, size=n)
    profit[rng.random(n) < 0.25] *= -1
    capex = np.where(rng.random(n) < 0.3, rng.uniform(0, 500_000, size=n), 0.0)
    rateable_value = np.where(rng.random(n) < 0.7, rng.uniform(0, 700_000, size=n), 0.0)
    turnover = rng.uniform(10_000, 5_000_000, size=n)
    # Some firms under the 90,000 registration threshold.
    standard_rated = turnover * rng.uniform(0, 1, size=n)
    standard_rated[: n // 10] = rng.uniform(0, 89_000, size=n // 10)
    input_vat = standard_rated * rng.uniform(0, 0.15, size=n)
    is_bank = np.zeros(n, dtype=bool)
    is_bank[[3, 7]] = True
    return pd.DataFrame(
        {
            "firm_id": np.arange(1, n + 1),
            "firm_weight": rng.uniform(1, 50, size=n),
            "firm_legal_form": legal_form,
            "firm_employees": employees,
            "firm_paybill": paybill,
            "firm_taxable_trading_profit": profit,
            "firm_capex_main_pool_new": capex,
            "firm_rateable_value": rateable_value,
            "firm_standard_rated_supplies": standard_rated,
            "firm_input_vat": input_vat,
            "firm_turnover": turnover,
            "firm_is_bank": is_bank,
        }
    )


def make_dataset(with_firms: bool) -> UKSingleYearDataset:
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2, 3, 4],
                "person_benunit_id": [1, 1, 2, 3],
                "person_household_id": [1, 1, 2, 3],
                "age": [40, 38, 70, 25],
                "employment_income": [45_000.0, 20_000.0, 0.0, 28_000.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2, 3]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2, 3],
                "household_weight": [1_000.0, 800.0, 1_200.0],
                "region": "LONDON",
                "rent": 0.0,
                "tenure_type": "OWNED_OUTRIGHT",
                "council_tax": 0.0,
                "corporate_sector_wealth": [100_000.0, 300_000.0, 0.0],
            }
        ),
        firm=firm_table() if with_firms else None,
        fiscal_year=YEAR,
    )


@pytest.fixture(scope="module")
def firms() -> pd.DataFrame:
    return firm_table()


@pytest.fixture(scope="module")
def sim():
    return Microsimulation(dataset=make_dataset(with_firms=True))


@pytest.fixture(scope="module")
def params(sim):
    return sim.tax_benefit_system.parameters(f"{YEAR}-04-06").gov.hmrc


def calc(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR), dtype=float)


def weighted(firms, values, mask=None):
    w = firms.firm_weight.values
    if mask is None:
        mask = np.ones(len(w), dtype=bool)
    return float((values * w)[mask].sum())


def test_corporation_tax_matches_hand_calculation(sim, params, firms):
    """Companies with no capital spending and a non-negative profit pay
    the small profits rate up to the lower limit, the main rate less
    marginal relief up to the upper limit, and the main rate above it.
    Companies with a loss pay none; other legal forms pay none."""
    p = params.corporation_tax
    company = firms.firm_legal_form.values == "COMPANY"
    profit = firms.firm_taxable_trading_profit.values
    no_capex = firms.firm_capex_main_pool_new.values == 0
    simple = company & no_capex & (profit >= 0)
    lower = p.marginal_relief.lower_limit
    upper = p.marginal_relief.upper_limit
    relief = p.marginal_relief.fraction * (upper - profit)
    expected = np.select(
        [profit <= lower, profit <= upper],
        [profit * p.small_profits_rate, profit * p.main_rate - relief],
        default=profit * p.main_rate,
    )
    ct = calc(sim, "corporation_tax")
    assert simple.sum() >= 20
    assert weighted(firms, ct, simple) == pytest.approx(
        weighted(firms, expected, simple), rel=TOL
    )
    loss = company & (profit < 0)
    assert loss.sum() > 0
    assert ct[loss] == pytest.approx(0)
    assert ct[~company] == pytest.approx(0)
    # Capital allowances only cut the tax.
    with_capex = company & ~no_capex & (profit >= 0)
    assert np.all(ct[with_capex] <= profit[with_capex] * p.main_rate + 1e-6)


def test_apprenticeship_levy_matches_hand_calculation(sim, params, firms):
    p = params.apprenticeship_levy
    expected = np.maximum(p.rate * firms.firm_paybill.values - p.allowance, 0)
    levy = calc(sim, "apprenticeship_levy")
    assert levy == pytest.approx(expected, rel=TOL, abs=0.01)
    assert weighted(firms, levy) == pytest.approx(weighted(firms, expected), rel=TOL)


def test_employer_ni_before_allowance_matches_hand_calculation(sim, params, firms):
    scale = params.national_insurance.class_1.employer_scale
    rate = scale.rates[1]
    annual_threshold = scale.thresholds[1] * 52
    expected = rate * np.maximum(
        firms.firm_paybill.values - firms.firm_employees.values * annual_threshold,
        0,
    )
    ni = calc(sim, "firm_employer_ni_before_allowance")
    assert ni == pytest.approx(expected, rel=TOL, abs=0.01)
    assert weighted(firms, ni) == pytest.approx(weighted(firms, expected), rel=TOL)


def test_business_rates_match_hand_calculation(sim, params, firms):
    """One occupied English property per firm, none retail, hospitality or
    leisure and no charities: the small, standard or high-value multiplier,
    then small business rate relief in full to the full relief threshold
    tapering to the taper end."""
    m = params.business_rates.multipliers
    sbrr = params.business_rates.reliefs.small_business
    rv = firms.firm_rateable_value.values
    multiplier = np.select(
        [rv >= m.high_value_threshold, rv < m.small_business_threshold],
        [m.high_value, m.small_business],
        default=m.standard,
    )
    gross = rv * multiplier
    relief_share = np.clip(
        (sbrr.taper_end_threshold - rv)
        / (sbrr.taper_end_threshold - sbrr.full_relief_threshold),
        0,
        1,
    )
    expected = gross * (1 - relief_share)
    rates = calc(sim, "firm_business_rates")
    assert rates == pytest.approx(expected, rel=TOL, abs=0.01)
    assert weighted(firms, rates) == pytest.approx(weighted(firms, expected), rel=TOL)


def test_vat_matches_hand_calculation(sim, params, firms):
    """Only standard-rated supplies: registered above the threshold, then
    output VAT at the standard rate less all input VAT."""
    p = params.vat
    supplies = firms.firm_standard_rated_supplies.values
    registered = supplies > p.registration.threshold
    expected = np.where(
        registered, supplies * p.standard_rate - firms.firm_input_vat.values, 0
    )
    assert (~registered).sum() > 0
    vat = calc(sim, "firm_vat")
    assert vat == pytest.approx(expected, rel=TOL, abs=0.01)
    assert weighted(firms, vat) == pytest.approx(weighted(firms, expected), rel=TOL)


def test_firm_tax_identity(sim):
    firm_tax = sim.tax_benefit_system.variables["firm_tax"]
    expected = sum(calc(sim, v) for v in firm_tax.adds) - sum(
        calc(sim, v) for v in firm_tax.subtracts
    )
    assert calc(sim, "firm_tax") == pytest.approx(expected, rel=TOL, abs=0.01)


def test_every_firm_variable_is_finite(sim):
    names = sorted(
        name
        for name, variable in sim.tax_benefit_system.variables.items()
        if variable.entity.key == "firm"
    )
    assert len(names) > 50
    not_finite = []
    for name in names:
        values = np.asarray(sim.calculate(name, YEAR))
        assert len(values) == N_FIRMS, name
        if values.dtype.kind in "fiub" and not np.all(np.isfinite(values)):
            not_finite.append(name)
    assert not_finite == []


@pytest.mark.parametrize("variable", ["gov_tax", "household_net_income"])
def test_firm_table_leaves_household_aggregates_unchanged(sim, variable):
    without_firms = Microsimulation(dataset=make_dataset(with_firms=False))
    with_firms = np.asarray(sim.calculate(variable, YEAR))
    assert with_firms == pytest.approx(
        np.asarray(without_firms.calculate(variable, YEAR)), abs=0.01
    )
