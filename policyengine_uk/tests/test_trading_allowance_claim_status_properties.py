"""Property tests for trading_allowance_claim_status (ITTOIA 2005 Part 6A,
Chapter 1).

Survey data hold profit, not receipts. The claim status says which receipts
lie behind a positive profit. A claimant's profit already deducts the
allowance legislated for the year the data were measured (here, a situation
whose status is supplied for the year simulated: £1,000 in 2026-27), so
their receipts are that profit plus £1,000. A non-claimant did not elect for
partial relief. Unknown, the default, keeps the rules for supplied or
missing receipts.

The reference below is written from the Act's options rather than from the
model's formula: full relief applies without an election whenever relevant
income is within the allowance (s. 783AE); partial relief needs an election
(s. 783AM), which a non-claimant has not made and a claimant has; ordinary
treatment deducts actual expenses and capital allowances, which for a
claimant partial relief replaced and are taken as a share of the input
allowance (gov.simulation.trading_allowance_claimant_expense_share), between
none and all of it. A claimant keeps the allowance while it does at least as
well for the trade as those expenses.

Invariants, each checked over many generated people in one reusable
simulation per allowance level and expense share:

1. Every status matches the reference: taxable trade profit, the Chapter 8
   deduction, Class 4 profits and whether the person takes the allowance.
2. A claimant's deductions never exceed the allowance's excess over £1,000,
   and with the default share a cut leaves their profit as reported.
3. A larger allowance never raises taxable trade profit, for any status.
4. A smaller expense share never lowers a claimant's taxable trade profit.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
# s. 783AD, the allowance for 2026-27, the year these situations are measured.
INPUT_ALLOWANCE = 1_000
ALLOWANCES = [0, 300, 500, 1_000, 2_000, 3_000, 5_000, 10_000]
# (allowance, claimant expense share): every allowance at the default share,
# and cuts at lower shares.
SCENARIOS = (
    [(allowance, 1.0) for allowance in ALLOWANCES]
    + [(allowance, share) for allowance in (0, 300, 500) for share in (0.0, 0.5)]
    # A share above 1 would put expenses above the allowance claimed.
    + [(1_000, 1.5)]
)
STATUSES = ["UNKNOWN", "CLAIMANT", "NON_CLAIMANT"]
PEOPLE = 30

amount = st.one_of(
    st.floats(min_value=0, max_value=12_000),
    st.floats(min_value=0, max_value=100_000),
    st.sampled_from([0.0, 300.0, 500.0, 999.99, 1_000.0, 2_000.0, 4_000.0]),
)
case = st.tuples(
    st.sampled_from(STATUSES),
    st.one_of(amount, st.floats(min_value=-3_000, max_value=0)),  # profit
    amount,  # actual expenses
    st.sampled_from(["unknown", "consistent", "below_profit"]),  # receipts
    st.sampled_from([0.0, 0.0, 150.0, 2_500.0]),  # capital allowances
    st.sampled_from([0.0, 0.0, 0.0, 300.0, 2_000.0]),  # losses brought forward
    st.one_of(amount, st.floats(min_value=-2_000, max_value=0)),  # misc income
    st.sampled_from([0.0, 0.0, 0.5, 1.0, 1.5]),  # Chapter 8 share of it
    st.sampled_from([0.0, 0.0, 0.0, 0.0, 300.0, 3_000.0]),  # current loss
)
cases = st.lists(case, min_size=PEOPLE, max_size=PEOPLE)


@pytest.fixture(scope="module")
def sims():
    people = {f"person_{i}": {"age": {YEAR: 40}} for i in range(PEOPLE)}
    situation = {
        "people": people,
        "benunits": {
            f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
        },
        "households": {
            f"household_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
        },
    }
    return {
        (allowance, share): Simulation(
            situation=situation,
            reform={
                "gov.hmrc.income_tax.allowances.trading_allowance": {
                    str(YEAR): allowance
                },
                "gov.simulation.trading_allowance_claimant_expense_share": {
                    str(YEAR): share
                },
            },
        )
        for allowance, share in SCENARIOS
    }


def run(sim, drawn):
    (
        status,
        profit,
        expenses,
        mode,
        capital,
        brought_forward,
        misc,
        chapter_8_share,
        loss,
    ) = (np.array(x) for x in zip(*drawn))
    receipts = np.select(
        [mode == "consistent", mode == "below_profit"],
        [np.maximum(profit, 0) + expenses, 0.5 * np.maximum(profit, 0)],
        0,
    )
    sim.set_input("trading_allowance_claim_status", YEAR, status)
    sim.set_input("self_employment_income", YEAR, profit)
    sim.set_input("self_employment_gross_receipts", YEAR, receipts)
    sim.set_input("capital_allowances", YEAR, capital)
    sim.set_input("loss_relief", YEAR, brought_forward)
    sim.set_input("miscellaneous_income", YEAR, misc)
    sim.set_input(
        "income_not_otherwise_charged",
        YEAR,
        chapter_8_share * np.maximum(misc, 0),
    )
    sim.set_input("trading_loss", YEAR, loss)
    sim.reset_calculations()

    # Compare against the stored (float32) inputs, not the float64 draws.
    def stored(name):
        return sim.calculate(name, YEAR).astype(float)

    return dict(
        status=status,
        profit=stored("self_employment_income"),
        receipts=stored("self_employment_gross_receipts"),
        capital=stored("capital_allowances"),
        brought_forward=stored("loss_relief"),
        misc=stored("miscellaneous_income"),
        chapter_8=stored("income_not_otherwise_charged"),
        loss=stored("trading_loss"),
        trade_relief=stored("trading_allowance_deduction"),
        chapter_8_relief=stored("miscellaneous_income_trading_allowance_deduction"),
        taxable=stored("taxable_self_employment_income"),
        class_4_profits=stored("ni_class_4_profits_before_losses"),
        uses=sim.calculate("uses_trading_allowance", YEAR),
    )


def reference(r, allowance, share):
    """Taxable trade profit, Class 4 profits, the Chapter 8 deduction and
    whether the person takes the allowance, from the Act's options."""
    profit, capital = r["profit"], r["capital"]
    brought_forward, loss = r["brought_forward"], r["loss"]
    # Chapter 8 income is part of miscellaneous income.
    chapter_8 = np.minimum(np.maximum(r["chapter_8"], 0), np.maximum(r["misc"], 0))
    trading = profit > 0
    claimant = trading & (r["status"] == "CLAIMANT")
    non_claimant = r["status"] == "NON_CLAIMANT"
    supplied = (r["receipts"] > 0) & (r["receipts"] >= profit)
    # Trade receipts. A claimant's profit is receipts less the input
    # allowance. Otherwise supplied receipts count; without them, no profit
    # means no receipts, a profit within the allowance means receipts equal
    # to it, and a non-claimant's profit (their expenses exceed the input
    # allowance) or a larger profit means receipts above any allowance.
    receipts = np.select(
        [claimant, supplied, ~trading, non_claimant | (profit > allowance)],
        [profit + INPUT_ALLOWANCE, r["receipts"], 0.0, np.inf],
        profit,
    )
    # Ordinary treatment deducts actual expenses and capital allowances; a
    # claimant's are a share of the input allowance, between none and all of
    # it, since they chose the allowance instead.
    claimant_expenses = min(max(share, 0), 1) * INPUT_ALLOWANCE
    ordinary = np.where(claimant, receipts - claimant_expenses, profit - capital)
    # Full relief (no election) or partial relief, trades first (s. 783AK).
    full = receipts + chapter_8 <= allowance
    with_allowance = np.where(full, 0, np.maximum(receipts - allowance, 0))
    chapter_8_relief = np.minimum(chapter_8, np.maximum(allowance - receipts, 0))
    # Partial relief needs an election, which a non-claimant has not made.
    available = full | ~non_claimant
    trade = np.where(available, np.minimum(with_allowance, ordinary), ordinary)
    chapter_8_relief = np.where(available, chapter_8_relief, 0)
    # A claimant's claim is their election: they keep the allowance while
    # there is one and it does at least as well for the trade as deducting
    # their expenses, and otherwise take ordinary treatment. A current loss
    # does not enter: their claim set it aside.
    claimant_takes = claimant & (allowance > 0) & (with_allowance <= ordinary)
    chapter_8_relief = np.where(claimant & ~claimant_takes, 0, chapter_8_relief)
    # Anyone else claims a current loss larger than the allowance's saving
    # instead (ss. 783AL, 783AM).
    saving = (
        np.maximum(ordinary - brought_forward, 0)
        - np.maximum(trade - brought_forward, 0)
        + chapter_8_relief
    )
    claims_loss = ~claimant & (loss > saving)
    trade = np.where(claims_loss, ordinary, trade)
    chapter_8_relief = np.where(claims_loss, 0, chapter_8_relief)
    takes_allowance = np.where(
        claimant,
        claimant_takes,
        ~claims_loss & ((ordinary - trade > 0) | (chapter_8_relief > 0)),
    )
    # The model sums in float32, so where the reference compares a sum with
    # a threshold it may land on the other side within rounding: a
    # non-claimant's relevant income against the allowance, anyone else's
    # supplied loss against the saving, and, for whether they take the
    # allowance, its advantage on the trade against nil. A claimant's choice
    # compares the allowances alone, exactly.
    margin = tolerance(r["receipts"], profit, chapter_8, allowance)
    finite = np.isfinite(receipts)
    near_full = non_claimant & finite
    near_full &= np.abs(np.where(finite, receipts, 0) + chapter_8 - allowance) <= margin
    near_loss = ~claimant & (loss > 0) & (np.abs(loss - saving) <= margin)
    advantage = np.where(np.isfinite(with_allowance), ordinary - with_allowance, -1)
    return dict(
        taxable=np.maximum(trade - brought_forward, 0),
        class_4_profits=np.maximum(trade, 0),
        chapter_8_relief=chapter_8_relief,
        uses=takes_allowance,
        fragile=near_full | near_loss,
        fragile_uses=near_full
        | near_loss
        | (~claimant & (np.abs(advantage) <= margin)),
    )


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(np.abs(v) for v in values)


SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(cases)
def test_every_status_matches_the_act(sims, drawn):
    for (allowance, share), sim in sims.items():
        r = run(sim, drawn)
        expected = reference(r, allowance, share)
        margin = tolerance(r["receipts"], r["profit"], r["chapter_8"], allowance)
        compared = ~expected["fragile"]
        for name in ("taxable", "class_4_profits", "chapter_8_relief"):
            assert (np.abs(r[name] - expected[name]) <= margin)[compared].all(), (
                name,
                allowance,
                share,
            )
        compared = ~expected["fragile_uses"]
        assert (r["uses"] == expected["uses"])[compared].all(), (allowance, share)


@SETTINGS
@given(cases)
def test_a_claimant_gets_only_the_allowances_excess_over_the_input_allowance(
    sims, drawn
):
    for (allowance, share), sim in sims.items():
        r = run(sim, drawn)
        claimant = (r["status"] == "CLAIMANT") & (r["profit"] > 0)
        # The deduction gives back the capital allowances deducted separately.
        relief = r["trade_relief"] + r["capital"] + r["chapter_8_relief"]
        excess = max(allowance - INPUT_ALLOWANCE, 0)
        assert (relief[claimant] <= excess + tolerance(allowance)).all(), allowance
        if allowance <= INPUT_ALLOWANCE and share == 1:
            reported = np.maximum(r["profit"] - r["brought_forward"], 0)
            assert (
                np.abs(r["taxable"] - reported)[claimant]
                <= tolerance(r["profit"])[claimant]
            ).all(), allowance


@SETTINGS
@given(cases)
def test_a_larger_allowance_never_raises_taxable_profit(sims, drawn):
    for share in (1.0, 0.5, 0.0):
        levels = sorted(a for a, s in SCENARIOS if s == share)
        taxable = [run(sims[(a, share)], drawn)["taxable"] for a in levels]
        for smaller, larger in zip(taxable, taxable[1:]):
            assert (larger <= smaller + tolerance(smaller)).all(), share


@SETTINGS
@given(cases)
def test_a_smaller_expense_share_never_lowers_a_claimants_taxable_profit(sims, drawn):
    for allowance in (0, 300, 500):
        taxable = [
            run(sims[(allowance, share)], drawn)["taxable"] for share in (1.0, 0.5, 0.0)
        ]
        for larger_share, smaller_share in zip(taxable, taxable[1:]):
            assert (smaller_share >= larger_share - tolerance(larger_share)).all()
