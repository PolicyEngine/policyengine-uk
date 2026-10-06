"""Statutory sick, maternity and paternity pay as Pension Credit earnings.

The State Pension Credit Regulations 2002 reg 17A(2)(h) and (i) make
statutory sick pay, statutory maternity pay and statutory paternity pay
earnings of an employed earner, and reg 15(1)(o) to (q) except them from the
social security benefits prescribed as income. Pension Credit counted none of
them, while pension-age Housing Benefit counted statutory sick and maternity
pay. Both Housing Benefit schemes count statutory paternity pay as earnings
too (HB Regs 2006 reg 35(1)(i); HB (SPC) Regs 2006 reg 35(1)(i)).

What the model taxes (read from the code, not changed here): income tax sees
statutory sick and maternity pay through employment_benefits, which
taxable_employment_income adds to employment income; it does not see
statutory paternity pay. Class 1 National Insurance sees all three:
ni_class_1_income adds them to employment income.

Invariants, for single people and couples over State Pension age in 2026
(invariant 2 also draws younger partners), with no dependants, renting from
the council, with capital of at most £10,000 so that neither scheme's tariff
income applies, and with a carer in some families so that the Carer's
Allowance and Carer Support Payment counted since #1952 are covered too:

1. Differential: Pension Credit and pension-age Housing Benefit assess the
   same income. Where Guarantee Credit is not paid, Housing Benefit income is
   above its zero floor and Pension Credit income is above its zero floor,

       pension_credit_income + pension_credit_earnings_disregard
       = housing_benefit_applicable_income
         + housing_benefit_applicable_income_disregard.

   Each side adds back its own earnings disregard because the two follow
   different schedules: SPC Regs Sch VI (5, 10 or 20 pounds a week, at most
   the claimant's and partner's net earnings) against HB (SPC) Regs Sch 4,
   and the model's Housing Benefit disregard is a flat amount that is not
   capped at earnings and is given whether or not there are earnings. Every
   other difference is excluded by the draws: no pension contributions,
   maintenance, maternity allowance or Sure Start maternity grant, and both
   measures deduct the same income tax and National Insurance of the
   claimant and partner.
2. Metamorphic: moving an amount between employment income and statutory
   sick or maternity pay of the same person changes nothing: Pension Credit
   earnings, the earnings disregard, Pension Credit income, Housing Benefit
   applicable income, income tax and National Insurance are all unchanged.
   Moving it to statutory paternity pay
   leaves Pension Credit earnings and National Insurance unchanged and changes
   Pension Credit income only through income tax, which does not see that
   pay: Pension Credit income plus the claimant's and partner's income tax and
   National Insurance plus the earnings disregard is unchanged where Pension
   Credit income is above its zero floor in both runs. (The disregard is added
   back because it is capped at net earnings, which are net of that tax.)
3. Monotonicity: Guarantee Credit never rises as any one statutory payment
   rises.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PENSIONS = np.arange(0, 20_001, 500)
PAY_STEPS = np.arange(0, 20_001, 500)
STATUTORY_PAY = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]
# 52 times the 2026-27 weekly rates (SI 2026/148 arts 8, 9 and 10).
ANNUAL_RATE = {
    "statutory_sick_pay": 123.25 * 52,
    "statutory_maternity_pay": 194.32 * 52,
    "statutory_paternity_pay": 194.32 * 52,
}
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
REGIONS = {
    "ENGLAND": "NORTH_WEST",
    "WALES": "WALES",
    "SCOTLAND": "SCOTLAND",
}


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


def maybe(strategy):
    return st.one_of(st.just(0.0), strategy)


@st.composite
def adult(draw, min_age=67):
    person = dict(
        age=draw(st.integers(min_age, 95)),
        state_pension=draw(money(12_000)),
        employment_income=draw(maybe(money(5_000))),
    )
    for pay in STATUTORY_PAY:
        person[pay] = draw(maybe(money(ANNUAL_RATE[pay])))
    return person


@st.composite
def family(draw, partner_min_age=67):
    adults = [draw(adult())]
    if draw(st.booleans()):
        adults.append(draw(adult(min_age=partner_min_age)))
    carer = draw(st.sampled_from([None] + list(range(len(adults)))))
    country = draw(st.sampled_from(list(REGIONS)))
    return dict(
        adults=adults,
        carer=carer,
        # The carer qualifies by caring hours or by a reported award.
        by_hours=draw(st.booleans()),
        country=country,
        rent=draw(money(12_000)),
        council_tax=draw(money(3_000)),
        savings=draw(maybe(money(10_000))),
    )


def situation(families, steps, vary):
    """Each family once per step; vary(i, step) returns family i's people."""
    people, benunits, households = {}, {}, {}
    for i, fam in enumerate(families):
        for k, step in enumerate(steps):
            names = []
            for j, inputs in enumerate(vary(i, step)):
                name = f"p{i}_{k}_{j}"
                person = {key: {YEAR: value} for key, value in inputs.items()}
                if j == fam["carer"]:
                    if fam["by_hours"]:
                        person["care_hours"] = {YEAR: 35}
                    else:
                        person["carers_allowance_reported"] = {YEAR: 1}
                people[name] = person
                names.append(name)
            benunits[f"b{i}_{k}"] = {"members": names}
            households[f"h{i}_{k}"] = {
                "members": names,
                "country": {YEAR: fam["country"]},
                "region": {YEAR: REGIONS[fam["country"]]},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "rent": {YEAR: fam["rent"]},
                "council_tax": {YEAR: fam["council_tax"]},
                "savings": {YEAR: fam["savings"]},
            }
    return {"people": people, "benunits": benunits, "households": households}


BENUNIT_VARIABLES = [
    "guarantee_credit",
    "pension_credit_earnings",
    "pension_credit_earnings_disregard",
    "pension_credit_income",
    "housing_benefit_eligible",
    "housing_benefit_applicable_income",
    "housing_benefit_applicable_income_disregard",
]
SUMMED_PERSON_VARIABLES = ["income_tax", "national_insurance"] + STATUTORY_PAY


def grid(families, steps, vary):
    simulation = Simulation(situation=situation(families, steps, vary))
    shape = (len(families), len(steps))
    g = {
        variable: np.asarray(simulation.calculate(variable, YEAR)).reshape(shape)
        for variable in BENUNIT_VARIABLES
    }
    # With no dependants, the benefit-unit sum is the claimant's and partner's.
    for variable in SUMMED_PERSON_VARIABLES:
        values = simulation.calculate(variable, YEAR, map_to="benunit")
        g[variable] = np.asarray(values).reshape(shape)
    return g


def with_private_pension(fam, pension):
    # All private pension goes to the first adult.
    return [
        dict(a, private_pension_income=float(pension) * (j == 0))
        for j, a in enumerate(fam["adults"])
    ]


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_pension_credit_and_housing_benefit_assess_the_same_statutory_pay(families):
    g = grid(
        families,
        PENSIONS,
        lambda i, pension: with_private_pension(families[i], pension),
    )
    for i, fam in enumerate(families):
        pc_income = g["pension_credit_income"][i]
        hb_income = g["housing_benefit_applicable_income"][i]
        compared = (
            (g["guarantee_credit"][i] <= 0)
            & g["housing_benefit_eligible"][i].astype(bool)
            & (hb_income > 0)
            & (pc_income > 0)
        )
        pension_credit = pc_income + g["pension_credit_earnings_disregard"][i]
        housing_benefit = (
            hb_income + g["housing_benefit_applicable_income_disregard"][i]
        )
        assert np.allclose(
            pension_credit[compared], housing_benefit[compared], atol=0.01
        ), (fam, pension_credit[compared], housing_benefit[compared])
        has_pay = g["statutory_sick_pay"][i] + g["statutory_maternity_pay"][i] + g["statutory_paternity_pay"][i] > 0  # TEMP-COUNT
        print("COUNT inv1", int(compared.sum()), int((compared & has_pay).sum()), int((compared & (g["statutory_paternity_pay"][i] > 0)).sum()), fam["carer"] is not None, len(compared))  # TEMP-COUNT


@st.composite
def moves(draw):
    """A family, one adult in it, a statutory payment and an amount to move."""
    fam = draw(family(partner_min_age=40))
    mover = draw(st.integers(0, len(fam["adults"]) - 1))
    pay = draw(st.sampled_from(STATUTORY_PAY))
    amount = draw(money(ANNUAL_RATE[pay]))
    return fam, mover, pay, amount


@PROPERTY_SETTINGS
@given(st.lists(moves(), min_size=1, max_size=4))
def test_moving_pay_between_wages_and_statutory_pay(cases):
    families = [fam for fam, _, _, _ in cases]

    def placed(as_statutory_pay):
        def vary(i, pension):
            fam, mover, pay, amount = cases[i]
            people = with_private_pension(fam, pension)
            source = pay if as_statutory_pay else "employment_income"
            people[mover] = dict(people[mover])
            people[mover][source] += amount
            return people

        return vary

    as_wages = grid(families, PENSIONS, placed(False))
    as_pay = grid(families, PENSIONS, placed(True))
    for i, (fam, mover, pay, amount) in enumerate(cases):
        context = (fam, mover, pay, amount)
        print("COUNT inv2", pay, len(PENSIONS), int(((as_wages["pension_credit_income"][i] > 0) & (as_pay["pension_credit_income"][i] > 0)).sum()), round(amount, 2), int(as_pay["national_insurance"][i].max() > 0), int(np.abs(as_pay["income_tax"][i] - as_wages["income_tax"][i]).max() > 0.01))  # TEMP-COUNT
        for variable in ["pension_credit_earnings", "national_insurance"]:
            assert np.allclose(
                as_wages[variable][i], as_pay[variable][i], atol=0.01
            ), (variable, context)
        if pay == "statutory_paternity_pay":
            # Income tax does not see statutory paternity pay.
            def before_tax(g):
                return (
                    g["pension_credit_income"][i]
                    + g["income_tax"][i]
                    + g["national_insurance"][i]
                    + g["pension_credit_earnings_disregard"][i]
                )

            compared = (as_wages["pension_credit_income"][i] > 0) & (
                as_pay["pension_credit_income"][i] > 0
            )
            assert np.allclose(
                before_tax(as_wages)[compared],
                before_tax(as_pay)[compared],
                atol=0.01,
            ), context
        else:
            for variable in [
                "income_tax",
                "pension_credit_earnings_disregard",
                "pension_credit_income",
                "housing_benefit_applicable_income",
            ]:
                assert np.allclose(
                    as_wages[variable][i], as_pay[variable][i], atol=0.01
                ), (variable, context)


@st.composite
def raises(draw):
    """A family, one adult in it and the statutory payment that rises."""
    fam = draw(family())
    earner = draw(st.integers(0, len(fam["adults"]) - 1))
    pay = draw(st.sampled_from(STATUTORY_PAY))
    pension = draw(st.sampled_from([0.0, 2_000.0, 6_000.0]))
    return fam, earner, pay, pension


@PROPERTY_SETTINGS
@given(st.lists(raises(), min_size=1, max_size=4))
def test_guarantee_credit_never_rises_with_statutory_pay(cases):
    families = [fam for fam, _, _, _ in cases]

    def vary(i, step):
        fam, earner, pay, pension = cases[i]
        people = with_private_pension(fam, pension)
        people[earner] = dict(people[earner], **{pay: float(step)})
        return people

    g = grid(families, PAY_STEPS, vary)
    for i, case in enumerate(cases):
        _, _, pay, _ = case
        assert np.all(np.diff(g[pay][i]) > 0), case
        steps = np.diff(g["guarantee_credit"][i])
        print("COUNT inv3", pay, len(steps), int((g["guarantee_credit"][i][:-1] > 0).sum()), int((steps < -0.01).sum()))  # TEMP-COUNT
        assert np.all(steps <= 0.01), (case, steps)
