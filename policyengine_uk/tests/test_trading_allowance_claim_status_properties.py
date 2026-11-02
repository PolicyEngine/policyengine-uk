"""Property tests for trading_allowance_claim_status (ITTOIA 2005 Part 6A,
Chapter 1).

Survey data hold profit, not receipts. The claim status says which receipts
lie behind a positive profit. A claimant's profit already deducts the
allowance legislated for the year the profit was measured (for a situation,
the year simulated: £1,000 in 2026-27), so their receipts are that profit
plus £1,000. A non-claimant did not elect for
partial relief. Unknown, the default, keeps the rules for supplied or
missing receipts.

The reference below is written from the Act's options rather than from the
model's formula: full relief applies without an election whenever relevant
income is within the allowance (s. 783AE); partial relief needs an election
(s. 783AM), which a non-claimant has not made and a claimant has; ordinary
treatment deducts actual expenses and capital allowances, which for a
claimant partial relief replaced and are taken as a share of the input
allowance (gov.simulation.trading_allowance_claimant_expense_share), or their
capital allowances if larger, never above the input allowance. Everyone who
can take the allowance takes it unless a supplied current loss is worth more
than its saving; a claimant's saving is over deducting their expenses, and
they take the allowance only where it covers those expenses.

Invariants, each checked over many generated people in one reusable
simulation per allowance level and expense share, all on one run of each
simulation per draw:

1. Every status matches the reference: taxable trade profit, the Chapter 8
   deduction, Class 4 profits and whether the person takes the allowance.
2. A claimant's deductions never exceed the allowance's excess over £1,000,
   and with the default share a cut leaves their profit as reported.
3. A larger allowance never raises taxable trade profit, nor Class 4
   profits, for any status.
4. A smaller expense share never lowers the taxable trade profit of a
   claimant with no supplied current loss. With one, it can move them from
   claiming the loss to the allowance, which lowers that profit but gives
   the loss up; the YAML cases check their income tax.
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
    st.sampled_from([0.0, 0.0, 0.0, 300.0, 2_000.0, 25_000.0]),  # losses b/f
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
        (allowance, share): changed(Simulation(situation=situation), allowance, share)
        for allowance, share in SCENARIOS
    }


def changed(simulation, allowance, share, year=YEAR):
    """The simulation with the allowance and expense share changed for the
    year. Changing the parameters of a built simulation skips the baseline a
    reform would build, which cuts the fixture's cost by about a third; the
    input allowance still comes from the unreformed tree."""
    simulation.apply_parameter_changes(
        {
            "gov.hmrc.income_tax.allowances.trading_allowance": {str(year): allowance},
            "gov.simulation.trading_allowance_claimant_expense_share": {
                str(year): share
            },
        }
    )
    return simulation


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
    # Ordinary treatment deducts actual expenses and capital allowances. A
    # claimant's are a share of the input allowance, in pennies, or their
    # capital allowances if larger, but never above the allowance they chose
    # instead.
    share_expenses = round(min(max(share, 0), 1) * INPUT_ALLOWANCE, 2)
    claimant_expenses = np.minimum(
        np.maximum(share_expenses, np.round(capital, 2)), INPUT_ALLOWANCE
    )
    ordinary = np.where(claimant, receipts - claimant_expenses, profit - capital)
    # Full relief (no election) or partial relief, trades first (s. 783AK).
    full = receipts + chapter_8 <= allowance
    with_allowance = np.where(full, 0, np.maximum(receipts - allowance, 0))
    chapter_8_relief = np.minimum(chapter_8, np.maximum(allowance - receipts, 0))
    # Partial relief needs an election, which a non-claimant has not made. A
    # claimant's option is the allowance's own figure; anyone else's keeps
    # actual deductions where those do better.
    available = full | ~non_claimant
    trade = np.where(
        available,
        np.where(claimant, with_allowance, np.minimum(with_allowance, ordinary)),
        ordinary,
    )
    chapter_8_relief = np.where(available, chapter_8_relief, 0)
    # Ordinary treatment wins where a supplied current loss is worth more
    # than the allowance's saving (ss. 783AL, 783AM). A claimant's saving is
    # over deducting their expenses, and they take the allowance only where
    # it does at least as well for the trade as those expenses: with losses
    # brought forward covering both, the saving ties at nil either way.
    saving = (
        np.maximum(ordinary - brought_forward, 0)
        - np.maximum(trade - brought_forward, 0)
        + chapter_8_relief
    )
    claims_loss = loss > saving
    covers = allowance >= claimant_expenses
    claimant_takes = claimant & (allowance > 0) & covers & ~claims_loss
    ordinary_treatment = np.where(claimant, ~claimant_takes, claims_loss)
    trade = np.where(ordinary_treatment, ordinary, trade)
    chapter_8_relief = np.where(ordinary_treatment, 0, chapter_8_relief)
    takes_allowance = np.where(
        claimant,
        claimant_takes,
        ~claims_loss & ((ordinary - trade > 0) | (chapter_8_relief > 0)),
    )
    # The model sums in float32, so where the reference compares a sum with
    # a threshold it may land on the other side within rounding: a
    # non-claimant's relevant income against the allowance, a loss against
    # the saving (for a claimant with no loss, a saving near nil unless the
    # allowance equals their expenses exactly), and, for whether anyone else
    # takes the allowance, its advantage on the trade against nil.
    margin = tolerance(r["receipts"], profit, chapter_8, allowance)
    finite = np.isfinite(receipts)
    near_full = non_claimant & finite
    near_full &= np.abs(np.where(finite, receipts, 0) + chapter_8 - allowance) <= margin
    # Exact ties: the allowance equal to the expenses, or losses brought
    # forward clearly absorbing both options, where both savings are nil.
    absorbed = (ordinary <= brought_forward - margin) & (
        with_allowance <= brought_forward - margin
    )
    exact_tie = claimant & (loss == 0) & ((allowance == claimant_expenses) | absorbed)
    near_loss = (loss > 0) | (claimant & covers)
    near_loss &= (np.abs(loss - saving) <= margin) & ~exact_tie
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
def test_every_status_matches_the_act_and_more_allowance_never_charges_more(
    sims, drawn
):
    # One run of each simulation per draw serves every invariant, which keeps
    # the test's CI time down.
    results = {}
    for (allowance, share), sim in sims.items():
        r = results[(allowance, share)] = run(sim, drawn)
        # 1. Every status matches the reference.
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
        # 2. A claimant's deductions never exceed the allowance's excess over
        # £1,000; the deduction gives back the capital allowances deducted
        # separately. With the default share a cut leaves their profit as
        # reported.
        claimant = (r["status"] == "CLAIMANT") & (r["profit"] > 0)
        relief = r["trade_relief"] + r["capital"] + r["chapter_8_relief"]
        excess = max(allowance - INPUT_ALLOWANCE, 0)
        assert (relief[claimant] <= excess + tolerance(allowance)).all(), allowance
        if allowance <= INPUT_ALLOWANCE and share == 1:
            reported = np.maximum(r["profit"] - r["brought_forward"], 0)
            assert (
                np.abs(r["taxable"] - reported)[claimant]
                <= tolerance(r["profit"])[claimant]
            ).all(), allowance
    # 3. A larger allowance never raises taxable trade profit, nor the
    # profits Class 4 charges before its own losses.
    for share in (1.0, 0.5, 0.0):
        levels = sorted(a for a, s in SCENARIOS if s == share)
        for name in ("taxable", "class_4_profits"):
            figures = [results[(a, share)][name] for a in levels]
            for smaller, larger in zip(figures, figures[1:]):
                assert (larger <= smaller + tolerance(smaller)).all(), (name, share)
    # 4. A smaller expense share never lowers the taxable profit of a
    # claimant with no supplied current loss.
    for allowance in (0, 300, 500):
        no_loss = results[(allowance, 1.0)]["loss"] == 0
        taxable = [results[(allowance, share)]["taxable"] for share in (1.0, 0.5, 0.0)]
        for larger_share, smaller_share in zip(taxable, taxable[1:]):
            assert (smaller_share >= larger_share - tolerance(larger_share))[
                no_loss
            ].all()


@pytest.mark.parametrize(
    "year,allowance,share",
    [(2026, 1_000, 1.0), (2026, 500, 0.5), (2027, 1_650, 0.55)],
)
def test_a_claimant_with_no_loss_takes_an_allowance_equal_to_their_expenses(
    year, allowance, share
):
    """Where the allowance equals a claimant's expenses the two options tie,
    and ties take the allowance. Over many profits, capital allowances below
    those expenses and losses brought forward, float arithmetic must not tip
    the tie: the input allowance is £1,000 in 2026-27 and £3,000 in 2027-28,
    and 0.55 x £3,000 is a hair above £1,650 in floating point."""
    rng = np.random.default_rng(2764)
    count = 500
    expenses = round(share * {2026: 1_000, 2027: 3_000}[year], 2)
    people = {f"person_{i}": {"age": {year: 40}} for i in range(count)}
    simulation = changed(
        Simulation(
            situation={
                "people": people,
                "benunits": {
                    f"b_{i}": {"members": [f"person_{i}"]} for i in range(count)
                },
                "households": {
                    f"h_{i}": {"members": [f"person_{i}"]} for i in range(count)
                },
            }
        ),
        allowance,
        share,
        year,
    )
    some = rng.random(count) < 0.5
    simulation.set_input(
        "self_employment_income", year, np.round(rng.uniform(0.01, 20_000, count), 2)
    )
    simulation.set_input(
        "capital_allowances", year, np.round(rng.uniform(0, expenses, count), 2) * some
    )
    simulation.set_input(
        "loss_relief", year, np.round(rng.uniform(0, 5_000, count), 2) * ~some
    )
    simulation.set_input(
        "trading_allowance_claim_status", year, np.array(["CLAIMANT"] * count)
    )
    assert simulation.calculate("uses_trading_allowance", year).all()
