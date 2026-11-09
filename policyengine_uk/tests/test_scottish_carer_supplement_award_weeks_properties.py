"""The Scottish Carer Supplement for each award week in which Carer Support
Payment is payable.

Regulation 14A of the Carer's Assistance (Carer Support Payment) (Scotland)
Regulations 2023 (SSI 2023/302): "An individual is entitled to Scottish Carer
Supplement for each award week in which Carer Support Payment is payable to
the individual." The Scottish Ministers set the weekly rates of the two
components in regulation 16(1) and (1A). The model holds annual amounts, so
scottish_carer_supplement counts the award weeks as

    min(52, max(carer_support_payment_pre_overlap, carer_support_payment) / rate)

where carer_support_payment is positive, and pays the weekly supplement rate
for each of them. It measures the amount against 52 weekly rates as the engine
stores them, so a full year's entitlement counts exactly 52 weeks.

Invariants, for single people aged 14 to 90 in each UK country, in each year
from 2024 to 2030:

1. Bounds: the supplement lies between 0 and 52 weekly supplement rates, as
   the engine stores that amount.
2. The supplement is positive exactly where carer_support_payment is
   positive, in years whose supplement rate is positive.
3. Differential: the supplement equals the rule rebuilt here from the drawn
   inputs, with the rates read from the parameters.
4. Monotonic: raising a supplied carer_support_payment never lowers the
   supplement.
5. Whole weeks: a supplied payment of k weekly rates, for k from 1 to 52,
   gives k weekly supplements, and a payment of 52 weekly rates or more
   gives 52.
6. Full year where the model computes the payment and the amount before the
   overlapping-benefit reduction: with neither carer_support_payment nor
   carer_support_payment_pre_overlap supplied, the supplement equals 52
   weekly supplement rates, as the engine stores that amount, where
   carer_support_payment is positive, and nothing elsewhere.
7. A reform that sets the weekly Carer Support Payment rate to zero leaves no
   supplement and raises no floating-point error.

Each example puts every drawn person in one simulation, with the same inputs
in each year, and checks every year. The reference rebuilds the entitlement
before the overlapping-benefit reduction as 52 weekly rates for a carer in
Scotland, from 2025, who reaches the minimum age, cares for the minimum hours
or reports Carer's Allowance, and would claim; the drawn people have no
earnings. A State Pension supplied directly overlaps in full. The engine
stores amounts in float32, so the reference rounds the amounts it compares to
float32. The differential and whole-week comparisons allow a tenth of a penny
for the rounding, which comes to under £0.0001 at these sizes; the other
invariants hold exactly.

A last test checks gov.contrib.policyengine.disable_simulated_benefits, which
makes a Scottish carer's reported Carer's Allowance their
carer_support_payment and leaves the amount before the reduction to the model.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system
from policyengine_uk.utils.scenario import Scenario

CSP = "gov.social_security_scotland.carer_support_payment"
WEEKS = 52
# carer_support_payment_pre_couple_limit pays Carer Support Payment from 2025.
CSP_FROM = 2025
YEARS = [2024, 2025, 2026, 2027, 2028, 2029, 2030]
# The years with a positive supplement rate.
SUPPLEMENT_YEARS = [2026, 2027, 2028, 2029, 2030]
COUNTRIES = ["ENGLAND", "WALES", "NORTHERN_IRELAND", "SCOTLAND"]
TOLERANCE = 0.001
# A State Pension equal to a year of Carer Support Payment in each year: under
# reg 16(2)(b), the payment given is then £0.
YEAR_OF_CSP = "a year of Carer Support Payment"
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False).map(
        lambda x: round(x, 2)
    )


# Up to about 72 weeks at the 2030 rate, small amounts of a week or two, and
# none.
PAYMENT = st.one_of(st.just(0.0), money(200), money(7_000))
# Below the 2025 to 2030 annual rates (4,331.60 to 5,018), above them, and
# equal to them.
STATE_PENSION = st.one_of(
    st.just(0.0), money(4_300), money(12_000), st.just(YEAR_OF_CSP)
)


def parameters(year):
    return system.parameters(year).gov.social_security_scotland.carer_support_payment


def stored(amount):
    """The amount as the engine stores it."""
    return float(np.float32(amount))


@st.composite
def batches(draw, supplied):
    """Single people aged 14 to 90, each in their own household, about half in
    Scotland.

    An input overrides its variable's formula for the whole population, so a
    batch supplies carer_support_payment for everyone (supplied) or for no
    one, and supplies carer_support_payment_pre_overlap for everyone or for no
    one.
    """
    give_pre_overlap = draw(st.sampled_from([False, False, True]))
    people = []
    for _ in range(draw(st.integers(2, 16))):
        person = {
            "country": draw(st.sampled_from(["SCOTLAND"] * 3 + COUNTRIES[:3])),
            "age": draw(st.integers(14, 90)),
            "care_hours": draw(st.sampled_from([0, 20, 34, 35, 40, 60])),
            "carers_allowance_reported": draw(st.sampled_from([0, 0, 0, 3_000])),
            "would_claim_carers_allowance": draw(st.sampled_from([True, True, False])),
        }
        if supplied:
            person["carer_support_payment"] = draw(PAYMENT)
        else:
            person["state_pension"] = draw(STATE_PENSION)
        if give_pre_overlap:
            person["carer_support_payment_pre_overlap"] = draw(PAYMENT)
        people.append(person)
    return people


def inputs(person, year):
    """The person's inputs in the year, with the sentinels replaced."""
    values = {key: value for key, value in person.items() if key != "country"}
    if values.get("state_pension") == YEAR_OF_CSP:
        values["state_pension"] = WEEKS * parameters(year).rate
    if "weeks_paid" in values:
        weeks_paid = values.pop("weeks_paid")
        values["carer_support_payment"] = weeks_paid * parameters(year).rate
    return values


def build(people, years=YEARS, reform=None):
    """One simulation holding every person, with inputs in each year."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, person in enumerate(people):
        by_year = {year: inputs(person, year) for year in years}
        situation["people"][f"p{i}"] = {
            name: {year: by_year[year][name] for year in years}
            for name in by_year[years[0]]
        }
        situation["benunits"][f"b{i}"] = {"members": [f"p{i}"]}
        situation["households"][f"h{i}"] = {
            "members": [f"p{i}"],
            "country": {year: person["country"] for year in years},
        }
    return Simulation(situation=situation, reform=reform)


def calc(sim, variable, year):
    return np.asarray(sim.calculate(variable, year), dtype=float)


def scheme(sim, year):
    parameters = sim.tax_benefit_system.parameters(year)
    return parameters.gov.social_security_scotland.carer_support_payment


def rates(sim, year):
    csp = scheme(sim, year)
    return float(csp.rate), float(csp.supplement)


def reference(sim, year, people):
    """The supplement rebuilt from the drawn inputs and the parameters."""
    csp = scheme(sim, year)
    rate, supplement = rates(sim, year)
    expected = []
    for person in people:
        values = inputs(person, year)
        if "carer_support_payment_pre_overlap" in values:
            pre_overlap = stored(values["carer_support_payment_pre_overlap"])
        else:
            eligible = (
                person["country"] == "SCOTLAND"
                and year >= CSP_FROM
                and person["age"] >= csp.min_age
                and (
                    person["care_hours"] >= csp.min_hours
                    or person["carers_allowance_reported"] > 0
                )
                and person["would_claim_carers_allowance"]
            )
            pre_overlap = stored(WEEKS * rate) if eligible else 0.0
        if "carer_support_payment" in values:
            payable = stored(values["carer_support_payment"])
        else:
            # Reg 16(2): the overlapping benefit reduces the payment, to £0
            # where the benefit equals or exceeds the payment.
            payable = max(pre_overlap - stored(values["state_pension"]), 0.0)
        weeks = min(WEEKS, max(pre_overlap, payable) / rate) if rate > 0 else 0.0
        expected.append(supplement * weeks if payable > 0 else 0.0)
    return np.array(expected)


def check_bounds_and_payment(sim, year):
    """Invariants 1 and 2."""
    supplement = calc(sim, "scottish_carer_supplement", year)
    payable = calc(sim, "carer_support_payment", year)
    rate, weekly_supplement = rates(sim, year)
    assert (supplement >= 0).all(), year
    assert (supplement <= np.float32(WEEKS * weekly_supplement)).all(), year
    if weekly_supplement > 0 and rate > 0:
        np.testing.assert_array_equal(supplement > 0, payable > 0, err_msg=str(year))
    else:
        np.testing.assert_array_equal(supplement, 0, err_msg=str(year))
    return supplement


def carer(country="ENGLAND", **values):
    """A 35-year-old with no caring inputs, who would claim."""
    return {
        "country": country,
        "age": 35,
        "care_hours": 0,
        "carers_allowance_reported": 0,
        "would_claim_carers_allowance": True,
        **values,
    }


def england(payment):
    return carer(carer_support_payment=payment)


def scottish_carer(payment, care_hours=40):
    return carer("SCOTLAND", care_hours=care_hours, carer_support_payment=payment)


def pensioner(state_pension, country="SCOTLAND"):
    return {
        **carer(country, care_hours=35, state_pension=state_pension),
        "age": 70,
    }


@PROPERTY_SETTINGS
@given(people=batches(supplied=True))
# 13 and 25 complete award weeks of the 2026 rate after a Sunday move to
# England (reg 42), one week, 60 weeks, a carer in Scotland with no caring
# inputs, and one the model finds eligible.
@example(
    people=[
        england(1_123.85),
        england(2_161.25),
        england(86.45),
        england(5_187),
        scottish_carer(1_123.85, care_hours=0),
        scottish_carer(1_123.85),
        scottish_carer(0),
    ]
)
# Both amounts supplied: a payment that State Pension reduced, none, and one
# week with no entitlement before the reduction.
@example(
    people=[
        carer(
            "SCOTLAND",
            carer_support_payment_pre_overlap=4_495.40,
            carer_support_payment=2_495.40,
        ),
        carer(carer_support_payment_pre_overlap=1_123.85, carer_support_payment=0),
        carer(carer_support_payment_pre_overlap=0, carer_support_payment=86.45),
    ]
)
def test_supplied_payment_bounds_and_reference(people):
    sim = build(people)
    for year in YEARS:
        supplement = check_bounds_and_payment(sim, year)
        # 3. Differential.
        np.testing.assert_allclose(
            supplement,
            reference(sim, year, people),
            atol=TOLERANCE,
            err_msg=str(year),
        )


@st.composite
def raised_batches(draw):
    people = draw(batches(supplied=True))
    raised = [
        {**person, "carer_support_payment": person["carer_support_payment"] + extra}
        for person, extra in zip(people, [draw(PAYMENT) for _ in people])
    ]
    return people, raised


@PROPERTY_SETTINGS
@given(batch=raised_batches())
def test_supplement_is_monotonic_in_a_supplied_payment(batch):
    people, raised = batch
    # One simulation: the drawn people, then the same people paid more.
    sim = build(people + raised)
    for year in YEARS:
        supplement = calc(sim, "scottish_carer_supplement", year)
        low, high = supplement[: len(people)], supplement[len(people) :]
        # 4. Exactly, since the formula rounds monotonically at each step.
        assert (high >= low).all(), year


def test_whole_weeks():
    """5. Each payment is a number of the year's weekly rates."""
    weeks = list(range(1, WEEKS + 1))
    beyond = [52, 52.001, 53, 60, 104, 1_000]
    # Carers in Scotland with no caring inputs have no entitlement before the
    # overlapping-benefit reduction either.
    people = [
        carer(COUNTRIES[i % len(COUNTRIES)], weeks_paid=k)
        for i, k in enumerate(weeks + beyond)
    ]
    sim = build(people, SUPPLEMENT_YEARS)
    for year in SUPPLEMENT_YEARS:
        _, weekly_supplement = rates(sim, year)
        expected = [k * weekly_supplement for k in weeks]
        expected += [WEEKS * weekly_supplement] * len(beyond)
        np.testing.assert_allclose(
            calc(sim, "scottish_carer_supplement", year),
            expected,
            atol=TOLERANCE,
            err_msg=str(year),
        )


@PROPERTY_SETTINGS
@given(people=batches(supplied=False))
# State Pension that reduces the payment and leaves some, that takes it to
# £0, and that equals it (reg 16(2)(b)); a carer outside Scotland.
@example(
    people=[
        pensioner(2_000),
        pensioner(6_000),
        pensioner(YEAR_OF_CSP),
        pensioner(0),
        pensioner(0, country="ENGLAND"),
    ]
)
def test_computed_payment_bounds_and_reference(people):
    sim = build(people)
    for year in YEARS:
        supplement = check_bounds_and_payment(sim, year)
        # 3. Differential.
        np.testing.assert_allclose(
            supplement,
            reference(sim, year, people),
            atol=TOLERANCE,
            err_msg=str(year),
        )
        if "carer_support_payment_pre_overlap" in people[0]:
            continue
        # 6. 52 weekly supplements, as the engine stores them, wherever the
        # model pays Carer Support Payment.
        payable = calc(sim, "carer_support_payment", year)
        _, weekly_supplement = rates(sim, year)
        full_year = (payable > 0) * weekly_supplement * WEEKS
        np.testing.assert_array_equal(
            supplement, full_year.astype(np.float32), err_msg=str(year)
        )


@pytest.mark.parametrize("supplied", [True, False])
def test_zero_rate_gives_no_supplement(supplied):
    """7. The formula guards the division by the weekly rate."""
    zero_rate = {f"{CSP}.rate": {"2024-01-01.2100-12-31": 0}}
    if supplied:
        people = [england(1_123.85), scottish_carer(1_123.85), england(0)]
    else:
        people = [pensioner(0), pensioner(2_000), pensioner(0, country="ENGLAND")]
    sim = build(people, SUPPLEMENT_YEARS, reform=zero_rate)
    for year in SUPPLEMENT_YEARS:
        assert rates(sim, year)[0] == 0
        # Calculate the inputs to the formula first, so that only the formula
        # runs with floating-point errors raised.
        calc(sim, "carer_support_payment", year)
        calc(sim, "carer_support_payment_pre_overlap", year)
        with np.errstate(all="raise"):
            supplement = calc(sim, "scottish_carer_supplement", year)
        np.testing.assert_array_equal(supplement, 0, err_msg=str(year))


REFORM_ON = Scenario(
    applied_before_data_load=True,
    parameter_changes={"gov.contrib.policyengine.disable_simulated_benefits": True},
)


def test_disable_simulated_benefits_pays_the_weeks_the_report_implies():
    """Two carers in Scotland, aged 40 and caring 40 hours a week, each report
    £4,000 of Carer's Allowance in 2025. The reform makes each report their
    carer_support_payment in every year, without uprating it. The model finds
    the carer who would claim eligible, so they keep 52 weeks; it finds the
    one who would not claim ineligible, so they get the weeks the report
    implies at each year's weekly rate."""
    years = range(2025, 2028)
    people = {
        name: {
            "age": {year: 40 for year in years},
            "care_hours": {year: 40 for year in years},
            "would_claim_carers_allowance": {year: claims for year in years},
            "carers_allowance_reported": {2025: 4_000},
        }
        for name, claims in [("claims", True), ("would_not_claim", False)]
    }
    situation = {
        "people": people,
        "benunits": {f"{name}_unit": {"members": [name]} for name in people},
        "households": {
            f"{name}_home": {
                "members": [name],
                "region": {year: "SCOTLAND" for year in years},
            }
            for name in people
        },
    }
    sim = Simulation(situation=situation, scenario=REFORM_ON)
    expected = {
        # 52 x 86.45 = 4,495.40 before the reduction. 52 x 11.70 = 608.40;
        # 4,000 / 86.45 = 46.27 weeks, x 11.70 = 541.35.
        2026: ([4_495.40, 0], [608.40, 4_000 / 86.45 * 11.70]),
        # 52 x 89.50 = 4,654 before the reduction. 52 x 12.10 = 629.20;
        # 4,000 / 89.50 = 44.69 weeks, x 12.10 = 540.78.
        2027: ([4_654, 0], [629.20, 4_000 / 89.50 * 12.10]),
    }
    for year, (pre_overlap, supplement) in expected.items():
        np.testing.assert_allclose(calc(sim, "carer_support_payment", year), 4_000)
        np.testing.assert_allclose(
            calc(sim, "carer_support_payment_pre_overlap", year),
            pre_overlap,
            atol=TOLERANCE,
            err_msg=str(year),
        )
        np.testing.assert_allclose(
            calc(sim, "scottish_carer_supplement", year),
            supplement,
            atol=TOLERANCE,
            err_msg=str(year),
        )
