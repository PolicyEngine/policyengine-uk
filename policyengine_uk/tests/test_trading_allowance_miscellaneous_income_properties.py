"""Property tests for the trading allowance on miscellaneous income
(ITTOIA 2005 Part 6A Chapter 1).

The allowance relieves the receipts of a person's relevant trades and their
"miscellaneous income", income chargeable under Part 5 Chapter 8 (income not
otherwise charged), before expenses (ss. 783A, 783AB and 783AC). One
allowance covers both. Within it, both are relieved in full (ss. 783AF and
783AG); above it, the person can elect to charge each source less a share of
the allowance, the shares adding up to the allowance, in place of actual
expenses (ss. 783AI-783AK). income_not_otherwise_charged is the part of
miscellaneous_income that is Chapter 8 income.

Invariants, each checked over many generated people in one reusable
simulation:

1. With trade receipts known, taxable trade profit plus taxable
   miscellaneous income equals the statutory figure: the lower of ordinary
   treatment and the allowance (differential against a reference written
   from the Act).
2. One allowance: the deductions from trade profits and from miscellaneous
   income never add up to more than the allowance.
3. Bounds: the miscellaneous deduction is between nil and the Chapter 8
   income, which counts up to positive miscellaneous income; taxable
   miscellaneous income is between nil and miscellaneous income.
4. The allowance's relief on trade profits does not depend on Chapter 8
   income when no current trading loss is supplied: the miscellaneous income
   gets only what the trade receipts leave.
5. With no Chapter 8 income nothing changes: no deduction, and taxable
   miscellaneous income is miscellaneous income with a loss counted as nil.
6. Means tests read the income before the allowance, whatever part of it is
   Chapter 8 income.
7. Income tax never rises as more of a person's miscellaneous income is
   Chapter 8 income.
8. Parity (differential): Chapter 8 income of X, with no trade, is charged
   the same income tax as trade receipts of X with no expenses.
9. A current trading loss is never both claimed and given up: when the
   allowance gives either relief, no current loss is relieved against
   general income or Class 4, and uses_trading_allowance says so.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
OTHER_EMPLOYMENT_INCOME = [0, 8_000, 30_000, 60_000, 110_000, 200_000]
CASES = 24
# Each case is simulated three times: as drawn, with no Chapter 8 income, and
# with all its positive miscellaneous income Chapter 8 income.
PEOPLE = 3 * CASES

amount = st.one_of(
    st.floats(min_value=0, max_value=3_500),
    st.floats(min_value=0, max_value=60_000),
    st.sampled_from([0.0, 400.0, 999.99, 1_000.0, 1_000.01, 3_000.0, 12_570.0]),
)
case = st.tuples(
    amount,  # trade profit
    amount,  # actual expenses
    st.sampled_from([0.0, 0.0, 150.0, 900.0]),  # capital allowances
    st.sampled_from(["unknown", "consistent", "none"]),  # receipts
    st.one_of(amount, st.floats(min_value=-2_000, max_value=0)),  # misc income
    st.floats(min_value=0, max_value=1.5),  # Chapter 8 share of misc income
    st.sampled_from([0.0, 0.0, 0.0, 300.0, 5_000.0]),  # current trading loss
)
cases = st.lists(case, min_size=CASES, max_size=CASES)


@pytest.fixture(scope="module")
def sim():
    people = {
        f"person_{i}": {
            "age": {YEAR: 40},
            "employment_income": {
                YEAR: OTHER_EMPLOYMENT_INCOME[i % CASES % len(OTHER_EMPLOYMENT_INCOME)]
            },
            "self_employment_income": {YEAR: 0},
            "self_employment_gross_receipts": {YEAR: 0},
            "capital_allowances": {YEAR: 0},
            "miscellaneous_income": {YEAR: 0},
            "income_not_otherwise_charged": {YEAR: 0},
            "trading_loss": {YEAR: 0},
        }
        for i in range(PEOPLE)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {
                f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
            "households": {
                f"household_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
        }
    )


OUTPUTS = [
    "trading_allowance_deduction",
    "miscellaneous_income_trading_allowance_deduction",
    "taxable_self_employment_income",
    "taxable_miscellaneous_income",
    "miscellaneous_income_before_trading_allowance",
    "uses_trading_allowance",
    "trade_loss_relief_against_general_income",
    "ni_class_4_trading_loss",
    "income_tax",
]


def run(sim, drawn, trade=True):
    """Simulate the drawn cases three times over (see PEOPLE). With
    ``trade`` false, the trade is dropped."""
    profit, expenses, capital_allowances, mode, misc, share, loss = map(
        np.array, zip(*drawn)
    )
    if not trade:
        profit = np.zeros_like(profit)
        expenses = np.zeros_like(expenses)
        capital_allowances = np.zeros_like(capital_allowances)
        mode = np.full_like(mode, "none")
    chapter_8 = np.concatenate(
        [share * np.maximum(misc, 0), np.zeros_like(misc), np.maximum(misc, 0)]
    )
    profit, expenses, capital_allowances, mode, misc, loss = (
        np.tile(x, 3) for x in (profit, expenses, capital_allowances, mode, misc, loss)
    )
    profit = np.where(mode == "none", 0, profit)
    receipts = np.where(mode == "consistent", profit + expenses, 0)
    sim.set_input("self_employment_income", YEAR, profit)
    sim.set_input("self_employment_gross_receipts", YEAR, receipts)
    sim.set_input("capital_allowances", YEAR, capital_allowances)
    sim.set_input("miscellaneous_income", YEAR, misc)
    sim.set_input("income_not_otherwise_charged", YEAR, chapter_8)
    sim.set_input("trading_loss", YEAR, loss)
    sim.reset_calculations()

    def stored(name):
        return sim.calculate(name, YEAR).astype(float)

    # Compare against the stored (float32) inputs, not the float64 draws.
    r = dict(
        profit=stored("self_employment_income"),
        receipts=stored("self_employment_gross_receipts"),
        capital_allowances=stored("capital_allowances"),
        misc=stored("miscellaneous_income"),
        chapter_8=stored("income_not_otherwise_charged"),
        loss=stored("trading_loss"),
        allowance=float(
            sim.tax_benefit_system.parameters(
                YEAR
            ).gov.hmrc.income_tax.allowances.trading_allowance
        ),
    )
    r["known"] = (r["receipts"] > 0) & (r["receipts"] >= r["profit"])
    r["expenses"] = np.maximum(r["receipts"] - r["profit"], 0)
    for name in OUTPUTS:
        r[name] = sim.calculate(name, YEAR)
    return r


def part(r, name, i):
    """The ith of the three copies of each case."""
    return r[name][i * CASES : (i + 1) * CASES]


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(np.abs(v) for v in values)


def statutory_taxable_income(r):
    """Taxable trade profit plus taxable miscellaneous income under Part 6A,
    with trade receipts known and no current trading loss.

    Ordinary treatment charges the profit after capital allowances (nil if
    they exceed it) and all positive miscellaneous income. Under the
    allowance, relevant income (receipts plus Chapter 8 income) within it is
    not charged; above it, relevant income less the allowance is charged,
    however the person splits it. Miscellaneous income outside Chapter 8 is
    charged either way. The person takes the lower.
    """
    allowance = r["allowance"]
    misc = np.maximum(r["misc"], 0)
    chapter_8 = np.minimum(np.maximum(r["chapter_8"], 0), misc)
    other = misc - chapter_8
    receipts = np.where(r["known"], r["receipts"], 0)
    ordinary = np.maximum(r["profit"] - r["capital_allowances"], 0) + misc
    relevant = receipts + chapter_8
    with_allowance = np.maximum(relevant - allowance, 0) + other
    return np.minimum(ordinary, with_allowance)


SETTINGS = settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(cases)
def test_taxable_income_matches_statutory_reference(sim, drawn):
    r = run(sim, drawn)
    # Known receipts or no trade, and no current loss to weigh.
    applies = (r["known"] | (r["profit"] == 0)) & (r["loss"] == 0)
    taxable = r["taxable_self_employment_income"] + r["taxable_miscellaneous_income"]
    expected = statutory_taxable_income(r)
    error = np.abs(taxable - expected)
    assert (
        error[applies]
        <= tolerance(r["receipts"], r["profit"], r["misc"], r["chapter_8"])[applies]
    ).all()


@SETTINGS
@given(cases)
def test_one_allowance_covers_both(sim, drawn):
    r = run(sim, drawn)
    total = (
        r["trading_allowance_deduction"]
        + r["miscellaneous_income_trading_allowance_deduction"]
    )
    assert (total <= r["allowance"] + tolerance(r["allowance"])).all()


@SETTINGS
@given(cases)
def test_deduction_and_taxable_income_are_bounded(sim, drawn):
    r = run(sim, drawn)
    deduction = r["miscellaneous_income_trading_allowance_deduction"]
    eligible = np.minimum(np.maximum(r["chapter_8"], 0), np.maximum(r["misc"], 0))
    assert (deduction >= 0).all()
    assert (deduction <= eligible + tolerance(eligible)).all()
    taxable = r["taxable_miscellaneous_income"]
    assert (taxable >= -tolerance(r["misc"])).all()
    assert (taxable <= np.maximum(r["misc"], 0) + tolerance(r["misc"])).all()


@SETTINGS
@given(cases)
def test_trade_relief_does_not_depend_on_chapter_8_income(sim, drawn):
    r = run(sim, drawn)
    no_loss = part(r, "loss", 0) == 0
    drawn_share = part(r, "trading_allowance_deduction", 0)
    none = part(r, "trading_allowance_deduction", 1)
    all_of_it = part(r, "trading_allowance_deduction", 2)
    assert np.allclose(drawn_share[no_loss], none[no_loss], atol=0.01)
    assert np.allclose(all_of_it[no_loss], none[no_loss], atol=0.01)


@SETTINGS
@given(cases)
def test_no_chapter_8_income_changes_nothing(sim, drawn):
    r = run(sim, drawn)
    misc = part(r, "misc", 1)
    np.testing.assert_array_equal(
        part(r, "miscellaneous_income_trading_allowance_deduction", 1), 0
    )
    np.testing.assert_allclose(
        part(r, "taxable_miscellaneous_income", 1),
        np.maximum(misc, 0),
        atol=0.01,
    )


@SETTINGS
@given(cases)
def test_means_tests_read_income_before_the_allowance(sim, drawn):
    r = run(sim, drawn)
    np.testing.assert_allclose(
        r["miscellaneous_income_before_trading_allowance"],
        np.maximum(r["misc"], 0),
        atol=0.01,
    )


@SETTINGS
@given(cases)
def test_income_tax_never_rises_with_more_chapter_8_income(sim, drawn):
    r = run(sim, drawn)
    # Without a current loss, whose opt-out weighs raw amounts, not tax.
    no_loss = part(r, "loss", 0) == 0
    none, drawn_share, all_of_it = (part(r, "income_tax", i) for i in (1, 0, 2))
    # The drawn share can exceed one, so order the two by the Chapter 8
    # income each copy actually has.
    more_than_all = part(r, "chapter_8", 0) > part(r, "chapter_8", 2)
    assert (drawn_share[no_loss] <= none[no_loss] + tolerance(none[no_loss])).all()
    lower = np.where(more_than_all, all_of_it, drawn_share)
    higher = np.where(more_than_all, drawn_share, all_of_it)
    assert (lower[no_loss] >= higher[no_loss] - tolerance(lower[no_loss])).all()


@SETTINGS
@given(st.lists(amount, min_size=CASES, max_size=CASES))
def test_chapter_8_income_is_taxed_like_trade_receipts(sim, amounts):
    amounts = np.array(amounts)
    zeros = np.zeros(CASES)
    # Copy 0: Chapter 8 income of X. Copy 1: receipts and profit of X.
    misc = np.concatenate([amounts, zeros, zeros])
    profit = np.concatenate([zeros, amounts, zeros])
    sim.set_input("self_employment_income", YEAR, profit)
    sim.set_input("self_employment_gross_receipts", YEAR, profit)
    sim.set_input("capital_allowances", YEAR, np.zeros(PEOPLE))
    sim.set_input("miscellaneous_income", YEAR, misc)
    sim.set_input("income_not_otherwise_charged", YEAR, misc)
    sim.set_input("trading_loss", YEAR, np.zeros(PEOPLE))
    sim.reset_calculations()
    tax = sim.calculate("income_tax", YEAR)
    np.testing.assert_allclose(
        tax[:CASES], tax[CASES : 2 * CASES], atol=float(tolerance(amounts).max())
    )


@SETTINGS
@given(cases)
def test_a_current_loss_is_never_both_claimed_and_given_up(sim, drawn):
    for trade in (True, False):
        r = run(sim, drawn, trade=trade)
        # Either relief, not only the trade's, means the allowance was used.
        used = (r["trading_allowance_deduction"] > 0) | (
            r["miscellaneous_income_trading_allowance_deduction"] > 0
        )
        assert (r["trade_loss_relief_against_general_income"][used] == 0).all()
        assert (r["ni_class_4_trading_loss"][used] == 0).all()
        # A loss larger than everything the allowance could save is claimed.
        saving_bound = r["allowance"] + tolerance(r["allowance"])
        assert not used[r["loss"] > saving_bound].any()
        np.testing.assert_array_equal(r["uses_trading_allowance"], used)
