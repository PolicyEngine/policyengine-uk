"""The gambling duty inputs grow with their duty's base, not its receipts (#2738).

Each input declares its duty's index under
``gov.economic_assumptions.indices.obr.gambling_duty_bases``, and dataset
projection grows it by the same ``yoy_growth`` series. A series is HMRC's
2024-25 and 2025-26 receipts, then the OBR's October 2026 forecast (receipts
Table 4.10), each year over the rate the model charges. For Machine Games
Duty that rate charges the higher-stake share of the standard-rate base at
the higher rate from 1 April 2027. Bases that give HMRC's 2024-25 receipts,
with the higher-stake input at that share, therefore give the OBR's receipts
in later years, and a rate reform moves receipts through the rate alone.
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.model_api import Scenario
from policyengine_uk.utils import import_obr_forecasts
from policyengine_uk.utils.import_obr_forecasts import (
    MACHINE_GAMES_HIGHER_STAKE_SHARE,
    RECEIPTS_SERIES_SPECS,
    line_rate,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

GROWTH = "gov.economic_assumptions.yoy_growth.obr.gambling_duty_bases"
INDEX = "gov.economic_assumptions.indices.obr.gambling_duty_bases"
INPUTS = {
    "general_betting": (
        "betting_exchange_commission",
        "financial_spread_betting_net_losses",
        "horse_and_dog_pool_betting_net_losses",
        "land_based_fixed_odds_betting_net_losses",
        "other_spread_betting_net_losses",
        "remote_other_betting_net_losses",
        "remote_uk_horseracing_betting_net_losses",
    ),
    "pool_betting": ("pool_betting_net_receipts",),
    "remote_gaming": ("remote_gaming_net_losses",),
    "machine_games": (
        "machine_games_higher_rate_net_takings",
        "machine_games_lower_rate_net_takings",
        "machine_games_standard_rate_higher_stake_net_takings",
        "machine_games_standard_rate_net_takings",
    ),
    "gaming": ("land_based_casino_net_losses",),
    "bingo": ("bingo_net_receipts",),
    "lottery": ("national_lottery_ticket_spending",),
}
DUTIES = {
    "general_betting": "general_betting_duty",
    "pool_betting": "pool_betting_duty",
    "remote_gaming": "remote_gaming_duty",
    "machine_games": "machine_games_duty",
    "gaming": "gaming_duty",
    "bingo": "bingo_duty",
    "lottery": "lottery_duty",
}
# OBR, Economic and fiscal outlook, October 2026, detailed forecast tables:
# receipts, Table 4.10 (£ billion), 2026-27 to 2031-32, as published.
TABLE_4_10 = {
    "remote_gaming": (2.7520296250837784, 2.7812750734699425, 2.8416867878041874, 2.9053716896455919, 2.9446821891345443, 2.963204761653297),
    "lottery": (0.83052038459597621, 0.84965566898040046, 0.87574553838772884, 0.90350845044750805, 0.92958587301870155, 0.95685079671453654),
    "general_betting": (0.65560522982822456, 0.87744453968275893, 0.91694664204685206, 0.94862995017184315, 0.97646741817020943, 1.0041740187990271),
    "machine_games": (0.67707068705786499, 0.82692873727074745, 0.85695449075649544, 0.86524127517297356, 0.87550370868921701, 0.89631020781238802),
    "gaming": (0.17422987982556123, 0.18488058456996015, 0.18523427331264838, 0.18548069649974164, 0.18650974968911124, 0.18568125218312026),
    "bingo": (1.8867652000000002e-4, 0.0, 0.0, 0.0, 0.0, 0.0),
    "pool_betting": (2.8288821260900035e-3, 2.6802893699237468e-3, 2.85842704577818e-3, 2.8371447589557743e-3, 2.9959073747097458e-3, 3.1258296515431082e-3),
}  # fmt: skip
# HMRC, UK Betting and Gaming Statistics, July 2026 tables,
# Table_1_BG_receipts rows 45 (2024-25) and 46 (2025-26), £ thousand.
HMRC = {
    "general_betting": (713_858, 684_502),
    "pool_betting": (8_125, 3_970),
    "remote_gaming": (1_162_539, 1_320_966),
    "machine_games": (609_245, 641_010),
    "gaming": (165_397, 173_902),
    "bingo": (25_233, 26_073),
    "lottery": (931_887, 980_132),
}
# The 2024-25 bases of the duties with more than one rate, in £ (Microcosm's
# national levels): General Betting Duty's split by Gambling Commission
# yield, and Machine Games Duty's bands from HMRC's liabilities over their
# rates. The remote part pays 25% from 1 April 2027; the rest 15%. From the
# same date the higher-stake part of the standard-rate band pays 25%.
GENERAL_BETTING_PARTS = {
    "remote_uk_horseracing_betting_net_losses": 888_079_509.7245454,
    "land_based_fixed_odds_betting_net_losses": 1_527_826_124.9133615,
    "horse_and_dog_pool_betting_net_losses": 55_219_132.22492455,
    "remote_other_betting_net_losses": 2_163_978_657.2782593,
    "betting_exchange_commission": 123_949_909.1922428,
}
MACHINE_GAMES_BANDS = {
    "machine_games_lower_rate_net_takings": (138_420_000, 0.05),
    "machine_games_standard_rate_net_takings": (3_023_740_000, 0.20),
    "machine_games_higher_rate_net_takings": (2_384_000, 0.25),
}
SINGLE_RATES = {
    "remote_gaming_net_losses": 0.21,
    "national_lottery_ticket_spending": 0.12,
    "pool_betting_net_receipts": 0.15,
    "land_based_casino_net_losses": 0.235487,
    "bingo_net_receipts": 0.10,
}
SINGLE_RATE_DUTY = {
    "remote_gaming_net_losses": "remote_gaming",
    "national_lottery_ticket_spending": "lottery",
    "pool_betting_net_receipts": "pool_betting",
    "land_based_casino_net_losses": "gaming",
    "bingo_net_receipts": "bingo",
}
REMOTE_SHARE = GENERAL_BETTING_PARTS["remote_other_betting_net_losses"] / sum(
    GENERAL_BETTING_PARTS.values()
)
STANDARD = "machine_games_standard_rate_net_takings"
HIGHER_STAKE = "machine_games_standard_rate_higher_stake_net_takings"
# The Gambling Commission's 2024-25 gaming machine yield, £ million, in
# Category B and in Category C (Industry Statistics, April 2025 to March 2026
# release, sheet 4, K34 and L34).
HIGHER_STAKE_SHARE = 2_289.84969448829 / (2_289.84969448829 + 232.47489298159996)


def machine_games_rate(higher_stake_rate, share=HIGHER_STAKE_SHARE):
    """Machine Games Duty's rate on its 2024-25 bands, with ``share`` of the
    standard-rate band at ``higher_stake_rate``."""
    total = sum(base for base, _ in MACHINE_GAMES_BANDS.values())
    charged = sum(base * rate for base, rate in MACHINE_GAMES_BANDS.values())
    standard = MACHINE_GAMES_BANDS[STANDARD][0]
    return (charged + standard * share * (higher_stake_rate - 0.20)) / total


MACHINE_GAMES_BEFORE = machine_games_rate(0.20)
MACHINE_GAMES_AFTER = machine_games_rate(0.25)
YEARS = range(2024, 2033)


@pytest.fixture(scope="module")
def parameters():
    return CountryTaxBenefitSystem().parameters


def index(parameters, duty, year):
    return parameters.get_child(f"{INDEX}.{duty}")(f"{year}-01-01")


def test_every_gambling_input_declares_its_duty_index():
    """Every input in the gambling folder declares its duty's index, and
    dataset projection grows it by the same duty's series."""
    from policyengine_uk.system import system

    folder = Path(__file__).parents[1] / "variables/input/consumption/gambling"
    inputs = {path.stem for path in folder.glob("*.py")}
    declared = {name: duty for duty, names in INPUTS.items() for name in names}
    assert set(declared) == inputs
    for name, duty in declared.items():
        assert system.variables[name].uprating == f"{INDEX}.{duty}", name
    mapping = yaml.safe_load(
        (Path(__file__).parents[1] / "data/uprating_indices.yaml").read_text()
    )
    gambling = {key: value for key, value in mapping.items() if "gambling" in key}
    assert gambling == {
        f"{GROWTH}.{duty}": list(names) for duty, names in INPUTS.items()
    }


def test_indices_are_positive_from_the_2024_base_year(parameters):
    for duty in INPUTS:
        assert index(parameters, duty, 2024) == 1
        for year in range(2024, 2040):
            assert index(parameters, duty, year) > 0, (duty, year)


def test_remote_gaming_index_takes_out_the_april_2026_rate_rise(parameters):
    """Receipts more than double into 2026-27 as the rate goes from 21% to
    40%; the base grows 9.4%."""
    receipts_growth = TABLE_4_10["remote_gaming"][0] / (HMRC["remote_gaming"][1] / 1e6)
    assert receipts_growth - 1 == pytest.approx(1.0834, abs=1e-4)
    base_growth = receipts_growth * 0.21 / 0.40
    growth = parameters.get_child(f"{GROWTH}.remote_gaming")
    assert growth("2026-01-01") == round(base_growth - 1, 6) == 0.093757
    assert index(parameters, "remote_gaming", 2026) / index(
        parameters, "remote_gaming", 2025
    ) == pytest.approx(base_growth, rel=2e-5)


def test_general_betting_index_takes_out_the_april_2027_remote_rise(parameters):
    """The remote part (45.5% of the 2024-25 base) goes from 15% to 25%, so
    the duty's rate on the whole base goes from 15% to 19.5%."""
    rate_2027 = 0.15 + 0.10 * REMOTE_SHARE
    assert rate_2027 == pytest.approx(0.19547, abs=1e-5)
    receipts = TABLE_4_10["general_betting"]
    base_growth = (receipts[1] / rate_2027) / (receipts[0] / 0.15)
    growth = parameters.get_child(f"{GROWTH}.general_betting")
    assert growth("2027-01-01") == round(base_growth - 1, 6) == 0.027038
    # Receipts grow 33.8%.
    assert receipts[1] / receipts[0] - 1 == pytest.approx(0.3384, abs=1e-4)


def test_the_higher_stake_share_is_category_b_over_b_and_c():
    assert MACHINE_GAMES_HIGHER_STAKE_SHARE == HIGHER_STAKE_SHARE
    assert HIGHER_STAKE_SHARE == pytest.approx(0.90783, abs=1e-5)


def test_machine_games_index_takes_out_the_april_2027_higher_stake_rise(parameters):
    """Table 4.10's Machine Games Duty line includes the Budget's higher rate
    on higher-stake machines (OBR paragraph 4.45): receipts grow 22.1% into
    2027-28. With 90.8% of the standard-rate base at 25%, the rate on the
    whole base goes from 19.35% to 23.68%, so the base falls 0.23%."""
    receipts = TABLE_4_10["machine_games"]
    assert receipts[1] / receipts[0] - 1 == pytest.approx(0.2213, abs=1e-4)
    assert MACHINE_GAMES_BEFORE == pytest.approx(0.193477, abs=1e-6)
    assert MACHINE_GAMES_AFTER == pytest.approx(0.236849, abs=1e-6)
    base_growth = (receipts[1] / MACHINE_GAMES_AFTER) / (
        receipts[0] / MACHINE_GAMES_BEFORE
    )
    growth = parameters.get_child(f"{GROWTH}.machine_games")
    assert growth("2027-01-01") == round(base_growth - 1, 6) == -0.002319


def test_bingo_base_holds_flat_once_its_rate_is_zero(parameters):
    """Bingo Duty ends on 1 April 2026; its base stays at its 2025-26 level."""
    at_2025 = index(parameters, "bingo", 2025)
    assert at_2025 == pytest.approx(HMRC["bingo"][1] / HMRC["bingo"][0], rel=1e-5)
    for year in range(2026, 2040):
        assert index(parameters, "bingo", year) == at_2025


def household_frame(year, inputs):
    """One household of one adult, with the given household inputs."""
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [40],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "council_tax": [0.0],
                "rent": [0.0],
                "household_weight": [1.0],
                **{name: [value] for name, value in inputs.items()},
            }
        ),
        fiscal_year=year,
    )


def situation(inputs, year=2024):
    return {
        "people": {"person": {"age": {year: 40}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                **{name: {year: value} for name, value in inputs.items()},
            }
        },
    }


ALL_INPUTS = {
    name: 1_000.0 * (position + 1)
    for position, name in enumerate(name for names in INPUTS.values() for name in names)
}


def test_dataset_projection_matches_core_uprating(parameters):
    """Two routes grow a 2024 input: dataset projection compounds the
    yoy_growth series a year at a time; Core scales a situation input by the
    ratio of the index (rounded to five decimals). They agree."""
    projected = extend_single_year_dataset(
        household_frame(2024, ALL_INPUTS), parameters, end_year=2032
    )
    simulation = Simulation(situation=situation(ALL_INPUTS))
    for year in YEARS:
        for name, value in ALL_INPUTS.items():
            stored = projected[year].household[name].iloc[0]
            uprated = simulation.calculate(name, year)[0]
            assert stored == pytest.approx(uprated, rel=1e-4), (name, year)
    # Remote gaming grows by the base series, not the receipts'.
    stored = projected[2026].household["remote_gaming_net_losses"].iloc[0]
    assert stored == pytest.approx(
        ALL_INPUTS["remote_gaming_net_losses"] * 1.136277 * 1.093757, rel=1e-6
    )


def test_higher_stake_machines_pay_the_april_2027_rise_once():
    """The Machine Games Duty series divides Table 4.10's line by the rate
    with the higher-stake rise in it, so the projected base holds no rise and
    the model adds it once (#2731): from model year 2027, 25% on the
    higher-stake part of the standard-rate base and 20% on the rest, both
    grown by the one index."""
    standard, higher_stake = STANDARD, HIGHER_STAKE
    simulation = Simulation(
        situation=situation({standard: 1_000.0, higher_stake: 400.0})
    )
    without = Simulation(situation=situation({standard: 1_000.0}))
    for year in range(2027, 2032):
        base = simulation.calculate(standard, year)[0]
        part = simulation.calculate(higher_stake, year)[0]
        assert base > 1_000
        # Inputs and duties are float32, and the rise is a difference of two.
        assert part == pytest.approx(0.4 * base, rel=1e-6)
        duty = simulation.calculate("machine_games_duty", year)[0]
        assert duty == pytest.approx(0.20 * (base - part) + 0.25 * part, rel=1e-6)
        rise = duty - without.calculate("machine_games_duty", year)[0]
        assert rise == pytest.approx(0.05 * part, rel=1e-5)


def test_a_rise_that_behaviour_offsets_leaves_the_duty_where_it_was():
    """£100 of higher-stake takings pay £20 at 20%. If the rise to 25%
    cuts them to £80, they pay the same £20, receipts hold flat, and the
    base index is 0.8: the model's 25% on the projected £80 gives the £20."""
    spec = import_obr_forecasts.machine_games_spec(1.0)
    rates = tuple(part for part in spec.rates if part.parameter.endswith("standard"))
    standard_only = import_obr_forecasts.ReceiptsSeriesSpec(
        path=spec.path, title=spec.title, row=spec.row, rates=rates
    )
    before, after = line_rate(standard_only, 2026), line_rate(standard_only, 2027)
    assert (before, after) == (0.20, 0.25)
    index = (20 / after) / (20 / before)
    assert index == pytest.approx(0.8, abs=1e-12)
    takings = 100 * index
    simulation = Simulation(
        situation=situation({STANDARD: takings, HIGHER_STAKE: takings}, year=2027)
    )
    assert simulation.calculate("machine_games_duty", 2027)[0] == pytest.approx(
        20, rel=1e-6
    )
    earlier = Simulation(situation=situation({STANDARD: 100, HIGHER_STAKE: 100}))
    assert earlier.calculate("machine_games_duty", 2024)[0] == pytest.approx(
        20, rel=1e-6
    )


def national_bases(higher_stake_share=HIGHER_STAKE_SHARE):
    """2024-25 bases that give HMRC's 2024-25 receipts at the model's rates,
    with the higher-stake input at ``higher_stake_share`` of the
    standard-rate input (none if None)."""
    bases = {
        name: HMRC[SINGLE_RATE_DUTY[name]][0] * 1e3 / rate
        for name, rate in SINGLE_RATES.items()
    }
    general_betting = HMRC["general_betting"][0] * 1e3 / 0.15
    total = sum(GENERAL_BETTING_PARTS.values())
    bases |= {
        name: general_betting * part / total
        for name, part in GENERAL_BETTING_PARTS.items()
    }
    machine_games = (
        HMRC["machine_games"][0]
        * 1e3
        / sum(base * rate for base, rate in MACHINE_GAMES_BANDS.values())
    )
    bases |= {
        name: base * machine_games for name, (base, _) in MACHINE_GAMES_BANDS.items()
    }
    if higher_stake_share is not None:
        bases[HIGHER_STAKE] = bases[STANDARD] * higher_stake_share
    return bases


def model_year_share(change: date, year: int) -> float:
    """The share of model year ``year`` (6 April to 5 April) from ``change``."""
    start, end = date(year, 4, 6), date(year + 1, 4, 6)
    after = max(start, min(change, end))
    return (end - after).days / (end - start).days


def expected_receipts(duty, year):
    """The duty in model year ``year`` on bases that give HMRC's 2024-25
    receipts: HMRC's receipts to 2025-26, then Table 4.10. Model years run
    6 April to 5 April, so those that take in five days of a 1 April rate
    change charge them at the new rate. Bingo Duty is zero from 2026-27,
    whatever late receipts Table 4.10 records."""
    if duty == "bingo" and year >= 2026:
        return 0.0
    if year < 2026:
        receipts = HMRC[duty][year - 2024] * 1e3
    else:
        receipts = TABLE_4_10[duty][min(year, 2031) - 2026] * 1e9
    if duty == "machine_games" and year == 2026:
        share = model_year_share(date(2027, 4, 1), 2026)
        receipts *= (
            MACHINE_GAMES_BEFORE * (1 - share) + MACHINE_GAMES_AFTER * share
        ) / MACHINE_GAMES_BEFORE
    if duty == "remote_gaming" and year == 2025:
        share = model_year_share(date(2026, 4, 1), 2025)
        receipts *= (0.21 * (1 - share) + 0.40 * share) / 0.21
    if duty == "bingo" and year == 2025:
        receipts *= 1 - model_year_share(date(2026, 4, 1), 2025)
    if duty == "general_betting" and year == 2026:
        share = model_year_share(date(2027, 4, 1), 2026)
        receipts *= (0.15 + 0.10 * REMOTE_SHARE * share) / 0.15
    return receipts


@pytest.fixture(scope="module")
def national_simulation():
    return Simulation(dataset=household_frame(2024, national_bases()))


@pytest.fixture(scope="module")
def national_simulation_without_higher_stake():
    return Simulation(dataset=household_frame(2024, national_bases(None)))


@pytest.mark.parametrize("duty", sorted(DUTIES))
def test_bases_that_give_hmrc_receipts_give_the_obr_forecast(national_simulation, duty):
    """Receipts are each base times its rate, and the bases grow by the
    OBR's receipts over those rates: so bases that give HMRC's 2024-25
    receipts give HMRC's 2025-26 receipts and then Table 4.10 in every year
    to 2031-32, with the higher-stake input at its share."""
    for year in range(2024, 2032):
        model = national_simulation.calculate(DUTIES[duty], year)[0]
        assert model == pytest.approx(expected_receipts(duty, year), rel=2e-4, abs=1), (
            duty,
            year,
        )


def test_without_the_higher_stake_input_the_duty_falls_short_of_table_4_10(
    national_simulation_without_higher_stake,
):
    """A dataset without the higher-stake input charges the standard rate on
    all of the standard-rate base, the rates before Budget 2026, while the
    base grows by receipts over the rates after it. From 2027-28 the duty is
    therefore Table 4.10's line times 19.35% / 23.68%, 18.3% short."""
    simulation = national_simulation_without_higher_stake
    assert 1 - MACHINE_GAMES_BEFORE / MACHINE_GAMES_AFTER == pytest.approx(
        0.1831, abs=1e-4
    )
    for year in range(2024, 2032):
        model = simulation.calculate("machine_games_duty", year)[0]
        expected = expected_receipts("machine_games", year)
        if year == 2026:
            expected = TABLE_4_10["machine_games"][0] * 1e9
        if year >= 2027:
            expected *= MACHINE_GAMES_BEFORE / MACHINE_GAMES_AFTER
        assert model == pytest.approx(expected, rel=2e-4, abs=1), year


# Each example builds a reform, which reprocesses the parameter tree.
@settings(max_examples=4, deadline=None, derandomize=True)
@given(
    bases=st.lists(
        st.floats(min_value=0, max_value=1e7, allow_nan=False),
        min_size=4,
        max_size=4,
    ),
    factor=st.floats(min_value=0.1, max_value=3, allow_nan=False),
    switch=st.booleans(),
    year=st.integers(min_value=2027, max_value=2031),
)
def test_a_rate_reform_moves_receipts_through_the_rate_alone(
    bases, factor, switch, year
):
    """Scaling the Remote Gaming Duty rate, the remote betting rate and the
    Machine Games Duty standard and higher rates for a year, and turning the
    higher-stake switch on or off, leaves every projected base as it was and
    moves each duty through its rates alone."""
    inputs = {
        "remote_gaming_net_losses": bases[0],
        "remote_other_betting_net_losses": bases[1],
        STANDARD: bases[2],
        HIGHER_STAKE: min(bases[3], bases[2]),
    }
    machine_games = "gov.hmrc.gambling_duty.machine_games"
    baseline = Simulation(situation=situation(inputs))
    reform = Simulation(
        situation=situation(inputs),
        scenario=Scenario(
            parameter_changes={
                "gov.hmrc.gambling_duty.remote_gaming.rate": {str(year): 0.40 * factor},
                "gov.hmrc.gambling_duty.general_betting.rates.remote": {
                    str(year): 0.25 * factor
                },
                f"{machine_games}.rates.standard": {str(year): 0.20 * factor},
                f"{machine_games}.rates.higher": {str(year): 0.25 * factor},
                f"{machine_games}.higher_stake_machines_at_higher_rate": {
                    str(year): switch
                },
            }
        ),
    )
    for name in inputs:
        np.testing.assert_array_equal(
            reform.calculate(name, year), baseline.calculate(name, year)
        )
    for name, duty in (
        ("remote_gaming_net_losses", "remote_gaming_duty"),
        ("remote_other_betting_net_losses", "general_betting_duty"),
    ):
        base = baseline.calculate(name, year)[0]
        before = baseline.calculate(duty, year)[0]
        after = reform.calculate(duty, year)[0]
        assert after == pytest.approx(before * factor, rel=1e-5, abs=0.05)
        rate = 0.40 if name == "remote_gaming_net_losses" else 0.25
        assert before == pytest.approx(base * rate, rel=1e-5, abs=0.05)
    standard = baseline.calculate(STANDARD, year)[0]
    part = baseline.calculate(HIGHER_STAKE, year)[0]
    before = baseline.calculate("machine_games_duty", year)[0]
    after = reform.calculate("machine_games_duty", year)[0]
    assert before == pytest.approx(
        0.20 * (standard - part) + 0.25 * part, rel=1e-5, abs=0.05
    )
    part_rate = 0.25 if switch else 0.20
    assert after == pytest.approx(
        factor * (0.20 * (standard - part) + part_rate * part), rel=1e-5, abs=0.05
    )


# A distinct rate for every rate parameter the duty formulas read, so a part
# of an importer series wired to the wrong parameter takes the wrong rate.
WIRING_RATES = {
    "gov.hmrc.gambling_duty.remote_gaming.rate": 0.31,
    "gov.hmrc.gambling_duty.lottery.rate": 0.17,
    "gov.hmrc.gambling_duty.general_betting.rates.fixed_odds": 0.11,
    "gov.hmrc.gambling_duty.general_betting.rates.remote": 0.29,
    "gov.hmrc.gambling_duty.general_betting.rates.exchange_commission": 0.43,
    "gov.hmrc.gambling_duty.general_betting.rates.financial_spread": 0.07,
    "gov.hmrc.gambling_duty.general_betting.rates.other_spread": 0.13,
    "gov.hmrc.gambling_duty.machine_games.rates.lower": 0.03,
    "gov.hmrc.gambling_duty.machine_games.rates.standard": 0.19,
    "gov.hmrc.gambling_duty.machine_games.rates.higher": 0.37,
    "gov.hmrc.gambling_duty.bingo.rate": 0.23,
    "gov.hmrc.gambling_duty.pool_betting.rate": 0.41,
    "household.consumption.gambling.casino_effective_rate": 0.47,
}
SWITCH = "gov.hmrc.gambling_duty.machine_games.higher_stake_machines_at_higher_rate"


def test_the_wiring_rates_cover_every_gambling_rate_parameter(parameters):
    """Every rate parameter under the gambling duties has a wiring rate,
    except Gaming Duty's statutory bands, an operator catalogue the household
    formula does not read."""
    leaves = {
        parameter.name
        for parameter in parameters.gov.hmrc.gambling_duty.get_descendants()
        if not hasattr(parameter, "children") and not hasattr(parameter, "brackets")
    }
    leaves = {name for name in leaves if ".gaming.normal_six_month_bands" not in name}
    assert leaves == set(WIRING_RATES) - {
        "household.consumption.gambling.casino_effective_rate"
    } | {SWITCH}


@pytest.mark.parametrize("switch", [True, False])
def test_each_series_charges_the_rates_the_model_charges(switch):
    """Differential: with every rate parameter set to its own value in
    2029-30, a household holding the national bases pays, over each duty's
    base, the rate the importer divides that duty's receipts by. The model's
    formulas decide which rate each input pays, so a part of a series wired
    to another parameter, or weighted as another part, fails."""
    year = 2029
    changes = {path: {str(year): rate} for path, rate in WIRING_RATES.items()}
    changes[SWITCH] = {str(year): switch}
    simulation = Simulation(
        dataset=household_frame(2024, national_bases()),
        scenario=Scenario(parameter_changes=changes),
    )
    values = {**WIRING_RATES, SWITCH: float(switch)}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            import_obr_forecasts,
            "parameter_values",
            lambda path: ((date(2000, 1, 1), values[path]),),
        )
        rates = {
            spec.path[-1]: line_rate(spec, year)
            for spec in RECEIPTS_SERIES_SPECS
            if spec.path[0] == "gambling_duty_bases"
        }
    assert rates.keys() == DUTIES.keys()
    for duty, names in INPUTS.items():
        base = sum(
            simulation.calculate(name, year)[0]
            for name in names
            if name != HIGHER_STAKE
        )
        charged = simulation.calculate(DUTIES[duty], year)[0]
        assert charged / base == pytest.approx(rates[duty], rel=1e-5), duty
