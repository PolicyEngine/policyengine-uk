"""Property tests for trading_allowance_claim_status (ITTOIA 2005 Part 6A,
Chapter 1).

Survey data hold profit, not receipts. The claim status says which receipts
lie behind it. A claimant's input profit already deducts the allowance in
force when it was measured (gov.simulation.trading_allowance_in_input_profits,
£1,000), so their receipts are that profit plus £1,000. A non-claimant deducts
actual expenses above £1,000. Unknown, the default, keeps the rules for
supplied or missing receipts.

Invariants, each checked over many generated people in one reusable
simulation per allowance level, from abolition to well above the £3,000 of
2027-28:

1. Every status matches a reference written from the Act. A claimant's
   taxable trade profit is the lower of ordinary treatment (the input profit,
   with expenses read as £1,000) and the allowance on receipts of profit plus
   £1,000, whatever receipts are supplied. Their income not otherwise charged
   gets what those receipts leave of the allowance. A non-claimant gets
   neither deduction. Unknown status gives what it gave before the status
   existed. A current loss larger than the allowance's saving is claimed
   instead.
2. A claimant's two deductions never exceed the allowance's excess over
   £1,000, so a cut to £1,000 or below leaves their profit as reported.
3. A larger allowance never raises taxable trade profit, for any status.
4. Class 4 reads the same deduction as income tax.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
INPUT_ALLOWANCE = 1_000
ALLOWANCES = [0, 500, 1_000, 2_000, 3_000, 5_000, 10_000]
STATUSES = ["UNKNOWN", "CLAIMANT", "NON_CLAIMANT"]
PEOPLE = 30

amount = st.one_of(
    st.floats(min_value=0, max_value=12_000),
    st.floats(min_value=0, max_value=100_000),
    st.sampled_from([0.0, 500.0, 999.99, 1_000.0, 2_000.0, 3_000.0, 4_000.0]),
)
case = st.tuples(
    st.sampled_from(STATUSES),
    st.one_of(amount, st.floats(min_value=-3_000, max_value=0)),  # profit
    amount,  # actual expenses
    st.sampled_from(["unknown", "consistent", "below_profit"]),  # receipts
    st.sampled_from([0.0, 0.0, 150.0, 2_500.0]),  # capital allowances
    st.sampled_from([0.0, 0.0, 0.0, 300.0, 2_000.0]),  # losses brought forward
    st.sampled_from([0.0, 0.0, 400.0, 900.0, 5_000.0]),  # Chapter 8 income
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
        allowance: Simulation(
            situation=situation,
            reform={
                "gov.hmrc.income_tax.allowances.trading_allowance": {
                    str(YEAR): allowance
                }
            },
        )
        for allowance in ALLOWANCES
    }


def run(sim, drawn):
    status, profit, expenses, mode, capital, brought_forward, chapter_8, loss = (
        np.array(x) for x in zip(*drawn)
    )
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
    sim.set_input("miscellaneous_income", YEAR, chapter_8)
    sim.set_input("income_not_otherwise_charged", YEAR, chapter_8)
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
        chapter_8=stored("income_not_otherwise_charged"),
        loss=stored("trading_loss"),
        trade_relief=stored("trading_allowance_deduction"),
        chapter_8_relief=stored("miscellaneous_income_trading_allowance_deduction"),
        taxable=stored("taxable_self_employment_income"),
        class_4_profits=stored("ni_class_4_profits_before_losses"),
    )


def reference(r, allowance):
    """Taxable trade profit and the Chapter 8 deduction, from the Act.

    Receipts within the allowance are fully relieved (s. 783AF). Above it the
    person takes the better of actual deductions and the allowance (s.
    783AI), and Chapter 8 income gets the part of the allowance the trade
    receipts leave (s. 783AK, trades first). Without receipts, a profit within
    the allowance is relieved in full and a larger one is taxed as reported.
    """
    profit, capital = r["profit"], r["capital"]
    claimant = r["status"] == "CLAIMANT"
    non_claimant = r["status"] == "NON_CLAIMANT"
    supplied = (r["receipts"] > 0) & (r["receipts"] >= profit)
    receipts = np.where(
        claimant, np.maximum(profit, 0) + INPUT_ALLOWANCE, r["receipts"]
    )
    known = claimant | supplied
    # A claimant's input profit is ordinary treatment with expenses of
    # £1,000: receipts less the input allowance.
    ordinary = profit - capital
    with_allowance = np.where(
        known,
        np.where(
            receipts <= allowance,
            0,
            np.minimum(ordinary, receipts - allowance),
        ),
        np.where(profit <= allowance, 0, ordinary),
    )
    with_allowance = np.where(non_claimant, ordinary, with_allowance)
    trade_saving = np.maximum(ordinary - with_allowance, 0)
    # The trade receipts that take up the allowance first.
    used = np.where(known, receipts, np.minimum(np.maximum(profit, 0), allowance))
    chapter_8_relief = np.where(
        non_claimant,
        0,
        np.minimum(r["chapter_8"], np.maximum(allowance - used, 0)),
    )
    # The election: a larger current loss is claimed instead (s. 783AL and
    # s. 783AM), and then neither deduction applies.
    saving = (
        np.minimum(trade_saving, np.maximum(ordinary - r["brought_forward"], 0))
        + chapter_8_relief
    )
    claim_loss = r["loss"] > saving
    taxable_before_losses = np.where(claim_loss, ordinary, ordinary - trade_saving)
    taxable = np.maximum(taxable_before_losses - r["brought_forward"], 0)
    return taxable, np.where(claim_loss, 0, chapter_8_relief)


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
def test_every_status_matches_the_act_at_every_allowance(sims, drawn):
    for allowance, sim in sims.items():
        r = run(sim, drawn)
        taxable, chapter_8_relief = reference(r, allowance)
        margin = tolerance(r["receipts"], r["profit"], allowance)
        assert (np.abs(r["taxable"] - taxable) <= margin).all(), allowance
        assert (np.abs(r["chapter_8_relief"] - chapter_8_relief) <= margin).all(), (
            allowance
        )


@SETTINGS
@given(cases)
def test_a_claimant_gets_only_the_allowances_excess_over_the_input_allowance(
    sims, drawn
):
    for allowance, sim in sims.items():
        r = run(sim, drawn)
        claimant = r["status"] == "CLAIMANT"
        relief = r["trade_relief"] + r["chapter_8_relief"]
        excess = max(allowance - INPUT_ALLOWANCE, 0)
        assert (relief[claimant] <= excess + tolerance(allowance)).all(), allowance
        if allowance <= INPUT_ALLOWANCE:
            reported = np.maximum(r["profit"] - r["capital"] - r["brought_forward"], 0)
            assert (
                np.abs(r["taxable"] - reported)[claimant]
                <= tolerance(r["profit"])[claimant]
            ).all(), allowance


@SETTINGS
@given(cases)
def test_a_larger_allowance_never_raises_taxable_profit(sims, drawn):
    taxable = [run(sims[allowance], drawn)["taxable"] for allowance in ALLOWANCES]
    for smaller, larger in zip(taxable, taxable[1:]):
        assert (larger <= smaller + tolerance(smaller)).all()


@SETTINGS
@given(cases)
def test_class_4_reads_the_same_deduction(sims, drawn):
    for allowance, sim in sims.items():
        r = run(sim, drawn)
        expected = np.maximum(r["profit"] - r["capital"] - r["trade_relief"], 0)
        assert (
            np.abs(r["class_4_profits"] - expected) <= tolerance(r["profit"])
        ).all(), allowance
