"""Property-based tests for the abolition of working-age Housing Benefit.

Working-age Housing Benefit awards outside specified and temporary
accommodation were abolished from 1 July 2026 in Great Britain (SI 2025/1148
art. 7, inserted by SI 2026/409) and 1 October 2026 in Northern Ireland
(SR 2025/176 art. 7, inserted by SR 2026/115). Claimants over the qualifying
age for State Pension Credit and protected mixed-age couples keep their awards
(art. 7(4)(a) and SI 2014/1230 reg 6A(4)-(5)).

Invariants, for any generated population of families:

1. Parameter: each fiscal year's working_age_awards_payable value equals the
   share of 6 April to 5 April falling before the statutory date, counted
   independently here from the two dates (1 before 2026-27, 0 after).
2. Bounds: 0 <= housing_benefit_payable_share <= 1, and it is 1 for every
   family with a member over State Pension age or the protected-accommodation
   input, in every model year.
3. Abolition: from 2027 no family without a member over State Pension age or
   the protected-accommodation input receives Housing Benefit, in any country
   or claim mode.
4. Differential against the pre-abolition rule: with working-age awards kept
   payable by a reform, Housing Benefit is what the continuing-award rule paid
   before. Under current law, Housing Benefit before the benefit cap is
   exactly that amount times the country's payable share for a family with no
   member over State Pension age or protected-accommodation input, and exactly
   the same amount for every other family (the cap applies afterwards, so the
   final amount is compared by 5).
   Mixed populations rarely hold a 2026 working-age continuing award, so a
   targeted test builds only those, for each year and jurisdiction.
5. Monotonic: the abolition never raises anyone's Housing Benefit and never
   changes Universal Credit.
6. Structural: only protected-accommodation families can get both Housing
   Benefit and Universal Credit, their UC housing costs element is zero,
   and Housing Benefit stays within 0 and the rent.
7. Default: omitting the protected-accommodation input produces the same
   Housing Benefit and Universal Credit outputs as setting it to False.
"""

import datetime

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
ABOLITION_DATES = {
    "great_britain": datetime.date(2026, 7, 1),
    "northern_ireland": datetime.date(2026, 10, 1),
}
PARAMETER = "gov.dwp.housing_benefit.working_age_awards_payable"
KEEP_WORKING_AGE_AWARDS = {
    f"{PARAMETER}.{jurisdiction}": {"2015-01-01.2040-12-31": 1}
    for jurisdiction in ABOLITION_DATES
}
REGIONS = ["LONDON", "NORTH_EAST", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
# State Pension age is 66 until the rise to 67 phases in from 2026-27; 68 and
# over is unambiguously pension age and 60 and under unambiguously working age.
PENSION_AGE = st.integers(68, 100)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single_pension": [("claimant", PENSION_AGE)],
    "mixed_age": [("claimant", PENSION_AGE), ("partner", WORKING_AGE)],
    "single_working": [("claimant", WORKING_AGE)],
    "couple_working": [("claimant", WORKING_AGE), ("partner", WORKING_AGE)],
    "pension_with_dependant": [
        ("claimant", PENSION_AGE),
        ("dependant", st.integers(18, 19)),
    ],
}
money = st.floats(0, 20_000, allow_nan=False, allow_infinity=False)


def fiscal_year_share_before(date, year):
    """Share of the fiscal year starting 6 April `year` falling before `date`."""
    start = datetime.date(year, 4, 6)
    end = datetime.date(year + 1, 4, 6)
    before = (min(max(date, start), end) - start).days
    return before / (end - start).days


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    return dict(
        shape=shape,
        members=[(role, draw(age)) for role, age in SHAPES[shape]],
        region=draw(st.sampled_from(REGIONS)),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(money),
        earnings=draw(st.one_of(st.just(0.0), money)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
        would_claim_uc=draw(st.booleans()),
        hb_reported=draw(st.sampled_from([0.0, 1.0])),
        in_specified_or_temporary_accommodation=draw(st.booleans()),
    )


def situation(units, year, claims_all):
    years = [year] if isinstance(year, int) else list(year)

    def annual(value):
        return {year: value for year in years}

    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, (role, age) in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            person = {"age": annual(age)}
            if role == "claimant":
                person["employment_income"] = annual(unit["earnings"])
                person["is_parent"] = annual(unit["shape"] == "pension_with_dependant")
                if unit["hb_reported"]:
                    person["housing_benefit_reported"] = annual(unit["hb_reported"])
            if role == "dependant":
                person["current_education"] = annual("UPPER_SECONDARY")
            people[name] = person
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": annual(unit["would_claim_uc"]),
            "in_specified_or_temporary_accommodation": annual(
                unit["in_specified_or_temporary_accommodation"]
            ),
            # claims_all_entitled_benefits sums reported benefits across the
            # whole simulation, so set it per family.
            "claims_all_entitled_benefits": annual(claims_all),
        }
        households[f"h{i}"] = {
            "members": names,
            "region": annual(unit["region"]),
            "rent": annual(unit["rent"]),
            "tenure_type": annual(unit["tenure"]),
            "savings": annual(unit["savings"]),
        }
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "housing_benefit",
    "housing_benefit_pre_benefit_cap",
    "housing_benefit_eligible",
    "housing_benefit_payable_share",
    "universal_credit",
    "uc_housing_costs_element",
    "benunit_rent",
]


def calculate(units, year, claims_all, reform=None):
    sim = Simulation(situation=situation(units, year, claims_all), reform=reform)
    return {v: np.asarray(sim.calculate(v, year)) for v in VARIABLES}


def any_over_pension_age(unit):
    return any(age >= 68 for _, age in unit["members"])


def jurisdiction(unit):
    return (
        "northern_ireland" if unit["region"] == "NORTHERN_IRELAND" else "great_britain"
    )


def check_structural(values, units):
    hb = values["housing_benefit"]
    protected = np.array(
        [unit["in_specified_or_temporary_accommodation"] for unit in units]
    )
    assert np.all(hb >= 0)
    assert np.all(hb <= values["benunit_rent"] + 0.01)
    assert not np.any((hb > 0) & (values["universal_credit"] > 0) & ~protected)
    assert np.all(values["uc_housing_costs_element"][protected] == 0)


@pytest.fixture(scope="module")
def baseline_tax_benefit_system():
    """Share immutable baseline parameters across the annual-value checks."""
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize("year", range(2015, 2041))
def test_payable_share_is_the_day_share_before_the_statutory_date(
    year, baseline_tax_benefit_system
):
    parameter = baseline_tax_benefit_system.parameters(
        str(year)
    ).gov.dwp.housing_benefit.working_age_awards_payable
    for name, date in ABOLITION_DATES.items():
        expected = fiscal_year_share_before(date, year)
        assert getattr(parameter, name) == pytest.approx(expected, abs=1e-12)


def test_day_shares_match_the_hand_counted_days():
    # 6 April to 30 June 2026 is 86 days; 6 April to 30 September is 178.
    assert fiscal_year_share_before(ABOLITION_DATES["great_britain"], 2026) == 86 / 365
    assert (
        fiscal_year_share_before(ABOLITION_DATES["northern_ireland"], 2026) == 178 / 365
    )


def test_dated_reform_is_blended_but_year_reform_covers_the_whole_fiscal_year():
    unit = dict(
        shape="single_working",
        members=[("claimant", 40)],
        region="LONDON",
        tenure="RENT_FROM_COUNCIL",
        rent=5_200,
        earnings=0,
        savings=0,
        would_claim_uc=False,
        hb_reported=1,
        in_specified_or_temporary_accommodation=False,
    )
    parameter = f"{PARAMETER}.great_britain"
    one_day = Simulation(
        situation=situation([unit], 2026, claims_all=False),
        reform={parameter: {"2026-07-01": 1}},
    )
    whole_year = Simulation(
        situation=situation([unit], 2026, claims_all=False),
        reform={parameter: {"2026": 1}},
    )
    # The single-date override adds one payable day to the baseline 86 days.
    assert one_day.calculate("housing_benefit_payable_share", 2026)[0] == pytest.approx(
        (86 + 1) / 365
    )
    assert whole_year.calculate("housing_benefit_payable_share", 2026)[0] == 1


@PROPERTY_SETTINGS
@given(
    st.lists(families(), min_size=1, max_size=25),
    st.sampled_from([2025, 2026, 2027, 2030]),
    st.booleans(),
)
def test_abolition_matches_the_pre_abolition_rule_scaled_by_the_payable_share(
    units, year, claims_all
):
    current = calculate(units, year, claims_all)
    kept = calculate(units, year, claims_all, reform=KEEP_WORKING_AGE_AWARDS)
    check_structural(current, units)
    check_structural(kept, units)
    share = current["housing_benefit_payable_share"]
    assert np.all((share >= 0) & (share <= 1))
    assert np.all(kept["housing_benefit_payable_share"] == 1)
    pre_cap = "housing_benefit_pre_benefit_cap"
    for i, unit in enumerate(units):
        if (
            any_over_pension_age(unit)
            or unit["in_specified_or_temporary_accommodation"]
        ):
            assert share[i] == 1, unit
            expected_share = 1
            assert current["housing_benefit"][i] == pytest.approx(
                kept["housing_benefit"][i], abs=0.01
            ), unit
        else:
            expected_share = fiscal_year_share_before(
                ABOLITION_DATES[jurisdiction(unit)], year
            )
            assert share[i] == pytest.approx(expected_share, abs=1e-9), unit
            if year >= 2027:
                assert current["housing_benefit"][i] == 0, unit
                assert not current["housing_benefit_eligible"][i], unit
        assert current[pre_cap][i] == pytest.approx(
            kept[pre_cap][i] * expected_share, abs=0.01
        ), unit
        assert current["housing_benefit"][i] <= kept["housing_benefit"][i] + 0.01
        assert current["universal_credit"][i] == pytest.approx(
            kept["universal_credit"][i], abs=0.01
        ), unit


@st.composite
def working_age_continuing_awards(draw, region):
    """A working-age family continuing an award: reported HB, no UC claim."""
    shape = draw(st.sampled_from(["single_working", "couple_working"]))
    return dict(
        shape=shape,
        members=[(role, draw(age)) for role, age in SHAPES[shape]],
        region=region,
        tenure=draw(st.sampled_from(TENURES[:3])),
        rent=draw(st.floats(1_000, 20_000, allow_nan=False, allow_infinity=False)),
        earnings=draw(st.one_of(st.just(0.0), money)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 15_000))),
        would_claim_uc=False,
        hb_reported=1.0,
        in_specified_or_temporary_accommodation=False,
    )


@pytest.mark.parametrize("year", [2025, 2026, 2027])
@pytest.mark.parametrize("region", ["LONDON", "NORTHERN_IRELAND"])
@settings(PROPERTY_SETTINGS, max_examples=5)
@given(data=st.data())
def test_working_age_continuing_award_is_paid_for_the_payable_share(year, region, data):
    # Every family here continues an award, and the first has no earnings, so
    # at least one has a positive entitlement in every example.
    units = data.draw(
        st.lists(working_age_continuing_awards(region), min_size=1, max_size=8)
    )
    units[0]["earnings"] = 0.0
    current = calculate(units, year, claims_all=False)
    kept = calculate(units, year, claims_all=False, reform=KEEP_WORKING_AGE_AWARDS)
    pre_cap = "housing_benefit_pre_benefit_cap"
    assert kept[pre_cap][0] > 0, units[0]
    expected_share = fiscal_year_share_before(
        ABOLITION_DATES[jurisdiction(units[0])], year
    )
    assert np.allclose(current["housing_benefit_payable_share"], expected_share)
    assert np.allclose(current[pre_cap], kept[pre_cap] * expected_share, atol=0.01)
    assert np.all(
        current["housing_benefit_eligible"]
        == (kept["housing_benefit_eligible"] & (expected_share > 0))
    )


@pytest.mark.parametrize("region", ["LONDON", "NORTHERN_IRELAND"])
@settings(PROPERTY_SETTINGS, max_examples=5)
@given(data=st.data())
def test_protected_working_age_award_is_payable_in_full_in_every_year(region, data):
    units = data.draw(
        st.lists(working_age_continuing_awards(region), min_size=1, max_size=8)
    )
    for unit in units:
        unit["in_specified_or_temporary_accommodation"] = True
    years = range(2015, 2041)
    sim = Simulation(situation=situation(units, years, claims_all=False))
    for year in years:
        share = sim.calculate("housing_benefit_payable_share", year)
        assert np.all(share == 1), (year, region, units)


@settings(PROPERTY_SETTINGS, max_examples=5)
@given(
    st.lists(families(), min_size=1, max_size=8),
    st.sampled_from([2025, 2026, 2027, 2030]),
    st.booleans(),
)
def test_omitted_accommodation_input_matches_explicit_false(units, year, claims_all):
    for unit in units:
        unit["in_specified_or_temporary_accommodation"] = False
    explicit = calculate(units, year, claims_all)
    omitted = situation(units, year, claims_all)
    for benunit in omitted["benunits"].values():
        benunit.pop("in_specified_or_temporary_accommodation")
    sim = Simulation(situation=omitted)
    for variable in VARIABLES:
        np.testing.assert_array_equal(
            sim.calculate(variable, year), explicit[variable], err_msg=variable
        )
