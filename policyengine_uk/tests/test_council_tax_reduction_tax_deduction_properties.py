"""Income tax and National Insurance deducted from Council Tax Reduction income.

Scotland's working-age scheme (the Council Tax Reduction (Scotland) Regulations
2021, SSI 2021/249) takes income tax and primary Class 1 contributions off
earnings only (regs 49(6)(b), 50(3)(a) and 51(2)); its unearned income rules
(regs 57 to 65) deduct no tax. The pensioner schemes disregard tax only on
income taken into account: SSI 2012/319 reg 31(12) in Scotland, SI 2012/2885
Sch 1 para 17(13) in England and WSI 2013/3029 Sch 1 para 11(13) in Wales.
council_tax_reduction_tax_deduction applies these rules, and
council_tax_reduction_applicable_income deducts it.

Each test builds single-adult households by hand in 2026, with no Universal
Credit claim, and states its invariant in its docstring.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
REGIONS = {"ENGLAND": "NORTH_WEST", "WALES": "WALES", "SCOTLAND": "SCOTLAND"}
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
WHOLE_TAX = ["income_tax_before_winter_fuel_payment_charge", "national_insurance"]
# Taxed income that is not earnings. A working-age adult has no State Pension.
UNEARNED = [
    "private_pension_income",
    "property_income",
    "savings_interest_income",
    "dividend_income",
]
# Taxed income the pensioner schemes do not take into account.
UNCOUNTED = [
    "savings_interest_income",
    "dividend_income",
    "scottish_carer_supplement",
]


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


def simulate(people, country):
    """One single-adult household per entry of people, all in one country."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, inputs in enumerate(people):
        name = f"p{i}"
        situation["people"][name] = {k: {YEAR: v} for k, v in inputs.items()}
        situation["benunits"][f"b{i}"] = {
            "members": [name],
            "would_claim_uc": {YEAR: False},
        }
        situation["households"][f"h{i}"] = {
            "members": [name],
            "country": {YEAR: country},
            "region": {YEAR: REGIONS[country]},
            "council_tax": {YEAR: 2_000.0},
            "savings": {YEAR: 0.0},
        }
    return Simulation(situation=situation)


def benunit_values(simulation, variable):
    return np.asarray(simulation.calculate(variable, YEAR))


def person_values(simulation, variables):
    return sum(
        np.asarray(simulation.calculate(v, YEAR, map_to="benunit")) for v in variables
    )


@st.composite
def working_age_adult(draw):
    return dict(
        age=draw(st.integers(25, 60)),
        employment_income=draw(st.one_of(st.just(0.0), money(80_000))),
        self_employment_income=draw(st.one_of(st.just(0.0), money(40_000))),
        **{v: draw(st.one_of(st.just(0.0), money(40_000))) for v in UNEARNED},
    )


@PROPERTY_SETTINGS
@given(
    st.lists(working_age_adult(), min_size=1, max_size=4),
    st.sampled_from(UNEARNED),
    money(30_000),
)
def test_scottish_working_age_income_never_falls_as_taxed_unearned_income_rises(
    adults, unearned, rise
):
    """In Scotland's working-age scheme, Council Tax Reduction applicable income
    never falls when a taxed unearned income rises and earnings stay fixed."""
    raised = [{**a, unearned: a[unearned] + rise} for a in adults]
    base = simulate(adults, "SCOTLAND")
    more = simulate(raised, "SCOTLAND")
    assert not benunit_values(base, "council_tax_reduction_pensioner").any()
    before = benunit_values(base, "council_tax_reduction_applicable_income")
    after = benunit_values(more, "council_tax_reduction_applicable_income")
    assert np.all(after >= before - 0.01), (adults, unearned, rise, before, after)


@PROPERTY_SETTINGS
@given(st.lists(working_age_adult(), min_size=1, max_size=4))
def test_scottish_working_age_deducts_no_tax_without_earnings(adults):
    """In Scotland's working-age scheme, with no earnings the deduction for
    income tax and National Insurance is nil, however much other taxed income
    there is."""
    no_earnings = [
        {**a, "employment_income": 0.0, "self_employment_income": 0.0} for a in adults
    ]
    simulation = simulate(no_earnings, "SCOTLAND")
    deduction = benunit_values(simulation, "council_tax_reduction_tax_deduction")
    assert np.all(deduction == 0), (no_earnings, deduction)


@st.composite
def pensioner(draw):
    # Pensions reach far enough, with the uncounted income, to cross the
    # personal allowance taper.
    return dict(
        age=draw(st.integers(67, 90)),
        state_pension=draw(money(12_000)),
        private_pension_income=draw(money(140_000)),
        property_income=draw(st.one_of(st.just(0.0), money(15_000))),
        savings_interest_income=draw(st.one_of(st.just(0.0), money(20_000))),
        dividend_income=draw(st.one_of(st.just(0.0), money(20_000))),
        scottish_carer_supplement=draw(st.sampled_from([0.0, 608.40])),
    )


@PROPERTY_SETTINGS
@given(
    st.lists(pensioner(), min_size=1, max_size=4),
    st.sampled_from(sorted(REGIONS)),
)
def test_pensioner_schemes_deduct_no_more_than_the_tax_on_counted_income(
    pensioners, country
):
    """In the pensioner schemes of England, Wales and Scotland, the income tax
    and National Insurance deducted never exceed what the same person would
    pay with only the income the scheme counts, nor the whole liability."""
    counted_only = [{**p, **{v: 0.0 for v in UNCOUNTED}} for p in pensioners]
    full = simulate(pensioners, country)
    alone = simulate(counted_only, country)
    assert benunit_values(full, "council_tax_reduction_pensioner").all()
    deduction = benunit_values(full, "council_tax_reduction_tax_deduction")
    tax_on_counted_income = person_values(alone, WHOLE_TAX)
    whole_tax = person_values(full, WHOLE_TAX)
    assert np.all(deduction <= tax_on_counted_income + 0.01), (
        pensioners,
        deduction,
        tax_on_counted_income,
    )
    assert np.all(deduction <= whole_tax + 0.01), (pensioners, deduction, whole_tax)
    # Taking away the uncounted income leaves the deduction where it was.
    deduction_alone = benunit_values(alone, "council_tax_reduction_tax_deduction")
    assert np.allclose(deduction, deduction_alone, atol=0.01), (
        pensioners,
        deduction,
        deduction_alone,
    )


CASES = [
    ("SCOTLAND", dict(age=40, employment_income=20_000.0, dividend_income=9_000.0)),
    ("SCOTLAND", dict(age=70, private_pension_income=15_000.0)),
    ("ENGLAND", dict(age=70, private_pension_income=20_308.0)),
    ("WALES", dict(age=70, private_pension_income=20_000.0)),
]


def test_council_tax_reduction_is_the_same_whichever_variable_is_calculated_first():
    """Council Tax Reduction and its tax deduction come out the same whether
    the deduction or the reduction is calculated first, so the deduction reads
    no benefit that depends on the reduction."""
    variables = [
        "council_tax_reduction_tax_deduction",
        "council_tax_reduction_applicable_income",
        "council_tax_reduction",
    ]
    for country, person in CASES:
        inputs = {**person, "savings_interest_income": 6_559.0}
        results = []
        for order in (variables, variables[::-1]):
            simulation = simulate([inputs], country)
            results.append(
                {v: float(simulation.calculate(v, YEAR).sum()) for v in order}
            )
        assert results[0] == results[1], (country, results)
