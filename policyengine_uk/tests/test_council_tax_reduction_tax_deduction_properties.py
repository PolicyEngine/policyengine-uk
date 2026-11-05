"""Income tax and National Insurance deducted from Council Tax Reduction income.

In Scotland's working-age scheme (the Council Tax Reduction (Scotland)
Regulations 2021, SSI 2021/249), the Scottish Ministers let the council take
income tax and primary Class 1 contributions off earnings only (regs 49(6)(b),
50(3)(a) and 51(2)), and give no tax deduction against unearned income (regs 57
to 65). Without Universal Credit, in reg 51(9) they apply the notional tax and
contributions of SSI 2012/303 reg 38 to self-employed profit. In the pensioner
schemes, the council disregards tax only on income taken into account and on
earnings: SSI 2012/319 regs 31(12), 33(2)(a) and 37 in Scotland, SI 2012/2885
Sch 1 paras 17(13), 19(2)(a) and 30 in England, and WSI 2013/3029 Sch 1 paras
11(13), 13(2)(a) and 24 in Wales.

No provision says how to split one income tax liability. The model follows
the choice settled for Pension Credit on PolicyEngine/policyengine-uk#2019
(option (a)): the tax on earnings is the extra tax the earnings cause, with
the earnings as the top slice of income. council_tax_reduction_tax_deduction
applies these rules, and council_tax_reduction_applicable_income deducts it.
In the English and Welsh working-age schemes, the formula deducts what the
legacy means tests deduct (legacy_means_test_deducted_income_tax).

Each test builds households by hand in 2026, states its invariant in its
docstring, and records the scheme of each household it draws as a Hypothesis
event, so that `--hypothesis-show-statistics` counts the examples per scheme.
"""

import numpy as np
from hypothesis import HealthCheck, event, example, given, settings
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
DEDUCTION = "council_tax_reduction_tax_deduction"
INCOME_TAX = "income_tax_before_winter_fuel_payment_charge"
NO_SCOTTISH_CARER_SUPPLEMENT = {
    "gov.social_security_scotland.carer_support_payment.supplement": {
        "2026-01-01.2100-12-31": 0
    }
}
# Taxed income the pensioner schemes do not count, as inputs.
UNCOUNTED = [
    "savings_interest_income",
    "other_investment_income",
    "dividend_income",
    "miscellaneous_income",
    "company_car_benefit",
]
# The same with the profits of a property business, which the strategies below
# draw on their own.
PENSIONER_UNCOUNTED = UNCOUNTED + ["property_income"]
# Taxed income other than earnings that Scotland's working-age scheme counts
# or treats as capital.
UNEARNED = [
    "private_pension_income",
    "property_income",
    "savings_interest_income",
    "dividend_income",
    "miscellaneous_income",
]


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


def maybe(high):
    return st.one_of(st.just(0.0), money(high))


def simulate(households, reform=None):
    """One simulation of households. Each household is a dict with country,
    benunits (a list of lists of person input dicts; the first benunit is
    the Council Tax Reduction applicant's) and, optionally, uc,
    child_benefit (whether the applicant's benefit unit claims Child
    Benefit) and council_tax (2,000 where the household gives none)."""
    situation = {"people": {}, "benunits": {}, "households": {}}
    for h, household in enumerate(households):
        names = []
        for b, adults in enumerate(household["benunits"]):
            members = []
            for p, inputs in enumerate(adults):
                name = f"p{h}_{b}_{p}"
                situation["people"][name] = {k: {YEAR: v} for k, v in inputs.items()}
                members.append(name)
            situation["benunits"][f"b{h}_{b}"] = {
                "members": members,
                "would_claim_uc": {YEAR: household.get("uc", False)},
            }
            if b == 0 and "child_benefit" in household:
                situation["benunits"][f"b{h}_{b}"]["would_claim_child_benefit"] = {
                    YEAR: household["child_benefit"]
                }
            names += members
        country = household["country"]
        situation["households"][f"h{h}"] = {
            "members": names,
            "country": {YEAR: country},
            "region": {YEAR: REGIONS[country]},
            "council_tax": {YEAR: household.get("council_tax", 2_000.0)},
            "savings": {YEAR: 0.0},
        }
    return Simulation(situation=situation, reform=reform)


def benunit_values(simulation, variable):
    return np.asarray(simulation.calculate(variable, YEAR))


def applicant_total(simulation, variable):
    """The Council Tax Reduction applicant's and partner's total, by benunit."""
    values = np.asarray(simulation.calculate(variable, YEAR))
    members = np.asarray(
        simulation.calculate("is_council_tax_reduction_applicant_or_partner", YEAR)
    )
    return np.asarray(
        simulation.map_result(values * members, "person", "benunit", how="sum")
    )


def scheme_of(country, pensioner, uc=False):
    if pensioner:
        return f"{country.lower()} pensioner"
    if country == "SCOTLAND":
        return "scotland working age " + ("with UC" if uc else "without UC")
    return f"{country.lower()} working age"


@st.composite
def adult(draw, pensioner, earnings=True, self_employment=True):
    person = dict(
        age=draw(st.integers(67, 90)) if pensioner else draw(st.integers(25, 60)),
        employment_income=draw(maybe(90_000)) if earnings else 0.0,
        self_employment_income=draw(maybe(90_000)) if self_employment else 0.0,
        private_pension_income=draw(maybe(60_000)),
        property_income=draw(maybe(30_000)),
        **{v: draw(maybe(40_000)) for v in UNCOUNTED},
    )
    if pensioner:
        person["state_pension"] = draw(money(12_000))
    return person


@st.composite
def household(draw, countries=tuple(REGIONS), pensioner=None, **kwargs):
    country = draw(st.sampled_from(countries))
    is_pensioner = draw(st.booleans()) if pensioner is None else pensioner
    adults = draw(st.lists(adult(is_pensioner, **kwargs), min_size=1, max_size=2))
    h = dict(country=country, benunits=[adults], pensioner=is_pensioner)
    if country == "SCOTLAND" and not is_pensioner and draw(st.booleans()):
        # A Universal Credit claim with two children, and earnings, profit,
        # pension and property income low enough for an award. Savings
        # interest, dividends and the other uncounted income stay as drawn:
        # Universal Credit does not count them.
        h["uc"] = True
        for a in adults:
            for variable in ["employment_income", "self_employment_income"]:
                a[variable] = min(a[variable], 10_000.0)
            a["private_pension_income"] = 0.0
            a["property_income"] = 0.0
        adults += [dict(age=4), dict(age=7)]
    return h


def grown_ups(people):
    """Indices of the adults among a benefit unit's members."""
    return [i for i, p in enumerate(people) if p["age"] >= 18]


def schemes(simulation, households):
    pensioner = benunit_values(simulation, "council_tax_reduction_pensioner")
    universal_credit = benunit_values(simulation, "universal_credit") > 0
    labels = []
    for i, h in enumerate(households):
        assert pensioner[i] == h["pensioner"], h
        labels.append(scheme_of(h["country"], pensioner[i], universal_credit[i]))
        event(labels[-1])
    return labels


@PROPERTY_SETTINGS
@given(
    st.lists(
        household(countries=("SCOTLAND",), pensioner=False, self_employment=False),
        min_size=1,
        max_size=4,
    )
)
def test_scottish_working_age_deduction_matches_pension_credit_earnings_tax(
    households,
):
    """Invariant 1. At working age in Scotland without self-employment income,
    the deduction less primary Class 1 contributions equals the income tax on
    employed earnings that Pension Credit computes
    (pension_credit_employment_income_tax), wherever the Council Tax
    Reduction applicant and partner are the Pension Credit claimant and
    partner."""
    simulation = simulate(households)
    schemes(simulation, households)
    same_people = np.asarray(
        simulation.calculate("is_council_tax_reduction_applicant_or_partner", YEAR)
    ) == np.asarray(simulation.calculate("is_claimant_or_partner", YEAR))
    assert same_people.all()
    deduction = benunit_values(simulation, DEDUCTION)
    class_1 = applicant_total(simulation, "ni_class_1_employee")
    pension_credit = benunit_values(simulation, "pension_credit_employment_income_tax")
    assert np.allclose(deduction - class_1, pension_credit, atol=0.01), (
        households,
        deduction,
        class_1,
        pension_credit,
    )


@PROPERTY_SETTINGS
@given(
    st.lists(household(pensioner=True, earnings=False), min_size=1, max_size=4),
    st.sampled_from(PENSIONER_UNCOUNTED),
    money(60_000),
    st.booleans(),
)
def test_pensioner_deduction_ignores_uncounted_income_without_earnings(
    households, uncounted, change, partner
):
    """Invariant 2. In every pensioner scheme, with no employed earnings, the
    deduction does not change when any uncounted income changes, for either
    member of a couple. The notional amount on self-employed profit reads the
    personal reliefs to which the person is entitled, which the uncounted
    income can taper, so the test compares the deduction less that amount."""
    changed = []
    for h in households:
        adults = [dict(a) for a in h["benunits"][0]]
        who = grown_ups(adults)[-1] if partner else 0
        adults[who][uncounted] = adults[who][uncounted] + change
        changed.append({**h, "benunits": [adults]})
    before = simulate(households)
    after = simulate(changed)
    schemes(before, households)

    def without_notional(simulation):
        notional = np.where(
            np.asarray([h["country"] == "SCOTLAND" for h in households], dtype=bool),
            applicant_total(
                simulation, "council_tax_reduction_scotland_self_employment_deductions"
            ),
            applicant_total(simulation, "pension_credit_self_employment_deductions"),
        )
        return benunit_values(simulation, DEDUCTION) - notional

    assert np.allclose(without_notional(before), without_notional(after), atol=0.01), (
        households,
        uncounted,
        change,
        without_notional(before),
        without_notional(after),
    )


@st.composite
def pensioner_parent_household(draw):
    """A pensioner family with one or two children and no employed earnings,
    each adult drawing a private pension of up to 120,000, so that the
    applicant's adjusted net income often exceeds the 60,000 at which the High
    Income Child Benefit Charge starts."""
    h = draw(household(pensioner=True, earnings=False))
    adults = h["benunits"][0]
    for a in adults:
        a["private_pension_income"] = draw(money(120_000))
    children = [dict(age=draw(st.integers(0, 15)))]
    if draw(st.booleans()):
        children.append(dict(age=draw(st.integers(0, 15))))
    return {**h, "benunits": [adults + children]}


@PROPERTY_SETTINGS
@given(st.lists(pensioner_parent_household(), min_size=1, max_size=4))
def test_pensioner_deduction_ignores_a_child_benefit_claim(households):
    """Invariant 2, for Child Benefit. In every pensioner scheme, with no
    employed earnings, the deduction does not change with a claim for Child
    Benefit. The pensioner schemes do not count Child Benefit, and through the
    High Income Child Benefit Charge HMRC recovers it, so the formula treats
    the charge as not tax payable on income taken into account. The test
    compares two simulations of the same families, one claiming Child Benefit
    and one not."""
    claiming = [{**h, "child_benefit": True} for h in households]
    not_claiming = [{**h, "child_benefit": False} for h in households]
    with_claim = simulate(claiming)
    without_claim = simulate(not_claiming)
    schemes(with_claim, households)
    charge = applicant_total(with_claim, "CB_HITC")
    for charged in charge > 0:
        event("High Income Child Benefit Charge" if charged else "no charge")
    assert np.all(benunit_values(with_claim, "child_benefit") > 0)
    assert np.all(benunit_values(without_claim, "child_benefit") == 0)
    assert np.allclose(
        benunit_values(with_claim, DEDUCTION),
        benunit_values(without_claim, DEDUCTION),
        atol=0.01,
    ), (
        households,
        charge,
        benunit_values(with_claim, DEDUCTION),
        benunit_values(without_claim, DEDUCTION),
    )


@st.composite
def any_household(draw):
    return draw(household())


@PROPERTY_SETTINGS
@given(st.lists(any_household(), min_size=1, max_size=4))
def test_deduction_bounds(households):
    """Invariant 3. The deduction never falls below zero. Without
    self-employment income it never exceeds the applicant's and partner's
    income tax before the winter fuel payment charge plus National Insurance.
    With it, the notional amount on profit can take the deduction above that
    liability, but never above the liability plus the notional amount."""
    simulation = simulate(households)
    schemes(simulation, households)
    deduction = benunit_values(simulation, DEDUCTION)
    whole = applicant_total(simulation, INCOME_TAX) + applicant_total(
        simulation, "national_insurance"
    )
    profit = applicant_total(simulation, "self_employment_income")
    notional = np.maximum(
        applicant_total(
            simulation, "council_tax_reduction_scotland_self_employment_deductions"
        ),
        applicant_total(simulation, "pension_credit_self_employment_deductions"),
    )
    assert np.all(deduction >= 0), (households, deduction)
    assert np.all((deduction <= whole + 0.01)[profit == 0]), (
        households,
        deduction,
        whole,
    )
    assert np.all(deduction <= whole + notional + 0.01), (
        households,
        deduction,
        whole,
        notional,
    )


@PROPERTY_SETTINGS
@given(
    st.lists(
        household(
            countries=("SCOTLAND",),
            pensioner=False,
            earnings=False,
            self_employment=False,
        ),
        min_size=1,
        max_size=4,
    )
)
def test_scottish_working_age_deducts_nothing_without_earnings(households):
    """Invariant 4. At working age in Scotland, with no earnings and no
    profit, the deduction is nil, however much other taxed income there is."""
    simulation = simulate(households)
    schemes(simulation, households)
    deduction = benunit_values(simulation, DEDUCTION)
    assert np.all(deduction == 0), (households, deduction)


@st.composite
def household_with_council_tax(draw, **kwargs):
    """A household from household(), with council tax of up to 30,000, so that
    families keep a reduction across the whole range of pay."""
    return {**draw(household(**kwargs)), "council_tax": draw(money(30_000))}


# The Hypothesis event invariant 5 records for each cliff or step it holds.
CROSSES = {
    "marriage_allowance": "crosses the Marriage Allowance cliff",
    "savings_allowance": "crosses a personal savings allowance cliff",
    "CB_HITC": "crosses a High Income Child Benefit Charge step",
    "personal_allowance": "crosses a personal allowance step",
}
# Invariant 5 runs these three families every time. A lone parent with two
# children whose pay of 10,000 rises by 1 takes adjusted net income from
# 64,999.50 to 65,000.50, across a step of the High Income Child Benefit
# Charge (560 to 584).
LONE_PARENT_AT_A_CHARGE_STEP = dict(
    country="SCOTLAND",
    pensioner=False,
    council_tax=2_000.0,
    benunits=[
        [
            dict(
                age=40,
                employment_income=10_000.0,
                savings_interest_income=40_000.0,
                other_investment_income=14_999.50,
            ),
            dict(age=4),
            dict(age=7),
        ]
    ],
)
# A single person with pay of 90,000 and savings interest of 20,001.75, whose
# pay rises by 0.50, takes adjusted net income across 110,002, where the
# tapered personal allowance falls from 7,570 to 7,569.
SINGLE_PERSON_AT_A_PERSONAL_ALLOWANCE_STEP = dict(
    country="SCOTLAND",
    pensioner=False,
    council_tax=30_000.0,
    benunits=[
        [dict(age=40, employment_income=90_000.0, savings_interest_income=20_001.75)]
    ],
)
# A single person whose pay rises from 13,000 to 14,000, within the Scottish
# starter band: the deduction rises by 190 of income tax and 80 of Class 1.
SINGLE_PERSON_IN_THE_STARTER_BAND = dict(
    country="SCOTLAND",
    pensioner=False,
    council_tax=2_000.0,
    benunits=[[dict(age=40, employment_income=13_000.0)]],
)


@PROPERTY_SETTINGS
@given(
    st.lists(
        household_with_council_tax(countries=("SCOTLAND",), pensioner=False),
        min_size=1,
        max_size=4,
    ),
    money(20_000),
    st.booleans(),
)
@example(households=[LONE_PARENT_AT_A_CHARGE_STEP], rise=1.0, partner=False)
@example(
    households=[SINGLE_PERSON_AT_A_PERSONAL_ALLOWANCE_STEP], rise=0.5, partner=False
)
@example(households=[SINGLE_PERSON_IN_THE_STARTER_BAND], rise=1_000.0, partner=False)
def test_scottish_working_age_reduction_never_rises_with_pay(households, rise, partner):
    """Invariant 5. At working age in Scotland without Universal Credit,
    raising either member's employment income never raises Council Tax
    Reduction once the test holds the income tax system's cliffs and steps
    still. Option (a) passes each of them through to the deduction, and each
    can raise the tax the earnings add by more than the rise in pay:
    - Marriage Allowance: an earner who enters the higher band loses the
      allowance, which the model takes off taxable income. A Scottish couple,
      one partner with no income and council tax of 15,000, whose pay rises
      from 43,661 to 43,663 loses 1,260 of it: the deduction rises by 265.39
      and the reduction by 52.68 (the YAML cases pin both).
    - The personal savings allowance: it falls from 1,000 to 500 as a person
      enters the higher band, and to nil in the additional band, so a pound
      of pay can bring 500 of savings income into tax at 40%, adding 200.
    - The High Income Child Benefit Charge: the model charges a whole
      percentage point of the Child Benefit for each whole 200 of adjusted
      net income above 60,000, so a pound of pay that crosses a step raises
      the charge by a percent of the Child Benefit, 23 or 24 pounds for two
      children.
    - The personal allowance: the model rounds the tapered allowance up to a
      whole pound, so a rise in pay of less than 2 can lower the allowance by
      a pound, and the tax then rises on the rise plus that pound.
    The test holds marriage_allowance, savings_allowance, CB_HITC and
    personal_allowance at their values before the rise in two more
    simulations, one of the families before the rise and one of the raised
    families, and asserts, for every family, that the reduction in the second
    does not exceed the reduction in the first. Because
    income_tax_with_inputs_zeroed keeps stored inputs on its branches, the
    branch without the pay then reads the same held values on both sides. The
    test draws council tax of up to 30,000, and always runs three families:
    a lone parent who crosses a step of the charge, a single person who
    crosses a step of the personal allowance, and a single person in the
    starter band."""
    raised = []
    for h in households:
        adults = [dict(a) for a in h["benunits"][0]]
        who = grown_ups(adults)[-1] if partner else 0
        adults[who]["employment_income"] += rise
        raised.append({**h, "uc": False, "benunits": [adults]})
    # The invariant is for families without Universal Credit.
    households = [{**h, "uc": False} for h in households]
    before = simulate(households)
    after = simulate(raised)
    # income_tax_with_inputs_zeroed keeps stored inputs on its branches, so
    # hold the cliffs and steps on both sides.
    held_before = simulate(households)
    held = simulate(raised)
    cliffs = [
        "marriage_allowance",
        "savings_allowance",
        "CB_HITC",
        "personal_allowance",
    ]
    for variable in cliffs:
        values = np.asarray(before.calculate(variable, YEAR))
        held_before.set_input(variable, YEAR, values)
        held.set_input(variable, YEAR, values)
    schemes(before, households)
    reduction_held_before = np.asarray(
        held_before.calculate("council_tax_reduction", YEAR)
    )
    reduction_held = np.asarray(held.calculate("council_tax_reduction", YEAR))
    # The model moves each of these in steps, so any change crosses one.
    crossed_any = np.zeros(len(households), dtype=bool)
    for variable in cliffs:
        crossed = ~np.isclose(
            applicant_total(before, variable), applicant_total(after, variable)
        )
        crossed_any |= crossed
        if crossed.any():
            event(CROSSES[variable])
    if not crossed_any.all():
        event("crosses no cliff or step")
    assert np.all(reduction_held <= reduction_held_before + 0.01), (
        households,
        rise,
        partner,
        reduction_held_before,
        reduction_held,
    )


@PROPERTY_SETTINGS
@given(
    st.lists(any_household(), min_size=1, max_size=3),
    adult(pensioner=False),
    adult(pensioner=False),
)
def test_non_dependant_income_never_changes_the_deduction(
    households, non_dependant, other_income
):
    """Invariant 6. A non-dependant's income never changes the deduction:
    adding a working-age adult with their own benefit unit to the household,
    and changing that adult's income, leaves the applicant's deduction where
    it was."""
    with_non_dependant = [
        {**h, "benunits": h["benunits"] + [[non_dependant]]} for h in households
    ]
    changed = [{**h, "benunits": h["benunits"] + [[other_income]]} for h in households]
    alone = simulate(households)
    schemes(alone, households)
    first = simulate(with_non_dependant)
    second = simulate(changed)
    # The applicant's benunit is the first in each household.
    applicant = np.arange(len(households)) * 2
    deduction = benunit_values(alone, DEDUCTION)
    for simulation in (first, second):
        assert np.allclose(
            benunit_values(simulation, DEDUCTION)[applicant], deduction, atol=0.01
        ), (households, non_dependant, other_income)


CASES = [
    dict(
        country="SCOTLAND",
        benunits=[[dict(age=40, employment_income=30_000.0, dividend_income=9_000.0)]],
    ),
    dict(
        country="SCOTLAND", benunits=[[dict(age=40, self_employment_income=15_000.0)]]
    ),
    dict(
        country="SCOTLAND",
        uc=True,
        benunits=[
            [
                dict(age=35, self_employment_income=15_000.0),
                dict(age=5),
                dict(age=3),
            ]
        ],
    ),
    dict(
        country="SCOTLAND", benunits=[[dict(age=70, private_pension_income=15_000.0)]]
    ),
    dict(
        country="ENGLAND",
        benunits=[[dict(age=70, employment_income=20_000.0)]],
    ),
    dict(
        country="WALES",
        benunits=[[dict(age=70, self_employment_income=60_000.0)]],
    ),
    dict(
        country="WALES",
        benunits=[[dict(age=40, employment_income=20_000.0)]],
    ),
]


def test_council_tax_reduction_is_the_same_whichever_variable_is_calculated_first():
    """Invariant 7. Council Tax Reduction and its tax deduction come out the
    same whether the deduction or the reduction is calculated first."""
    variables = [
        DEDUCTION,
        "council_tax_reduction_applicable_income",
        "council_tax_reduction",
    ]
    for case in CASES:
        applicant = case["benunits"][0][0]
        inputs = {
            **case,
            "benunits": [
                [{**applicant, "savings_interest_income": 6_559.0}]
                + case["benunits"][0][1:]
            ],
        }
        results = []
        for order in (variables, variables[::-1]):
            simulation = simulate([inputs])
            results.append(
                {v: float(simulation.calculate(v, YEAR).sum()) for v in order}
            )
        assert results[0] == results[1], (case, results)


UNCOUNTED_CASES = [
    ("savings_interest_income", 10_000.0),
    ("other_investment_income", 10_000.0),
    ("dividend_income", 10_000.0),
    ("miscellaneous_income", 10_000.0),
    ("company_car_benefit", 10_000.0),
    ("property_income", 10_000.0),
]


def test_branch_takes_each_uncounted_income_out_of_income_tax():
    """The pensioner schemes' tax on other counted income zeroes each income
    they do not count, so it equals the income tax of the same person without
    that income. This covers the Scottish Carer Supplement, which the model
    computes from the carer's award rather than reading as an input."""
    base = dict(age=70, private_pension_income=30_000.0)
    with_income = [
        dict(country="ENGLAND", benunits=[[{**base, variable: amount}]])
        for variable, amount in UNCOUNTED_CASES
    ]
    without_income = [dict(country="ENGLAND", benunits=[[base]])]
    branch = np.asarray(
        simulate(with_income).calculate(
            "council_tax_reduction_income_tax_on_other_counted_income", YEAR
        )
    )
    expected = float(simulate(without_income).calculate(INCOME_TAX, YEAR)[0])
    assert np.allclose(branch, expected, atol=0.01), (branch, expected)
    tax_with_income = np.asarray(simulate(with_income).calculate(INCOME_TAX, YEAR))
    assert np.all(tax_with_income > expected + 1), tax_with_income

    # A landlord's finance costs earn a 20% tax reduction on the rent. The
    # branch drops the reduction with the rent, so it gives the same tax with
    # or without the costs.
    landlords = simulate(
        [
            dict(
                country="ENGLAND",
                benunits=[
                    [
                        {
                            **base,
                            "property_income": 10_000.0,
                            "property_finance_costs": costs,
                        }
                    ]
                ],
            )
            for costs in (0.0, 5_000.0)
        ]
    )
    landlord_tax = np.asarray(landlords.calculate(INCOME_TAX, YEAR))
    assert np.isclose(landlord_tax[0] - landlord_tax[1], 1_000, atol=0.01)
    assert np.allclose(
        landlords.calculate(
            "council_tax_reduction_income_tax_on_other_counted_income", YEAR
        ),
        expected,
        atol=0.01,
    )

    carer = dict(
        age=70,
        private_pension_income=14_000.0,
        care_hours=35,
        would_claim_carers_allowance=True,
    )
    carer_household = [dict(country="SCOTLAND", benunits=[[carer]])]
    with_supplement = simulate(carer_household)
    without_supplement = simulate(carer_household, reform=NO_SCOTTISH_CARER_SUPPLEMENT)
    assert with_supplement.calculate("scottish_carer_supplement", YEAR)[0] > 0
    assert np.isclose(
        with_supplement.calculate(
            "council_tax_reduction_income_tax_on_other_counted_income", YEAR
        )[0],
        without_supplement.calculate(INCOME_TAX, YEAR)[0],
        atol=0.01,
    )
    assert (
        with_supplement.calculate(INCOME_TAX, YEAR)[0]
        > without_supplement.calculate(INCOME_TAX, YEAR)[0] + 1
    )


@PROPERTY_SETTINGS
@given(
    st.lists(
        household(countries=("ENGLAND", "WALES"), pensioner=False),
        min_size=1,
        max_size=4,
    )
)
def test_other_schemes_deduct_the_legacy_means_test_measure(households):
    """Invariant 8. In the English and Welsh working-age schemes, the
    deduction equals what the legacy means tests deduct: the applicant's and
    partner's legacy_means_test_deducted_income_tax, with the sum floored at
    nil, plus their National Insurance. So these schemes take no tax on the
    interest, dividends or rent from property that they do not count, beyond
    the extra tax that earnings cause on it."""
    simulation = simulate(households)
    schemes(simulation, households)
    expected = np.maximum(
        0, applicant_total(simulation, "legacy_means_test_deducted_income_tax")
    ) + applicant_total(simulation, "national_insurance")
    deduction = benunit_values(simulation, DEDUCTION)
    assert np.allclose(deduction, expected, atol=0.01), (
        households,
        deduction,
        expected,
    )
