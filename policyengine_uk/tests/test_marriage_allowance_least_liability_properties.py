"""The least liability under the Marriage Allowance rate test, against the law.

A married recipient in London whose partner has no income. The oracle works
the law itself (ITA 2007 ss. 10-13A, 12B, 16, 23, 25(2)/(3A), 55B), reading only
rate and allowance values from the parameter tree. The model holds incomes in
float32 and sums them in float32, so the income it tests can sit a fraction of
a penny (under a penny here) either side of the amounts drawn. So the oracle
applies the rate test twice: strictly, with every limit a penny lower, and
loosely, with every limit a penny higher. For every drawn recipient:

1. at the model's own share, the model's income tax equals the oracle's Step 5
   tax less the reduction where the model gives it; the model gives it wherever
   the strict test passes and Step 5 leaves tax, and nowhere the loose test
   fails;
2. the model's income tax is no more than the least liability under the
   strict test over every share on a grid, the thin sets where the rate test
   holds and the shares at the limit, and no more than the old order's.

Check 1 bounds the tax from below: it is the law's liability at a share the
model holds. Between the strict and loose tests the law itself lets income
reach each limit (s. 10(2)).
The explicit examples are recipients for whom only a share at a limit
qualifies.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

K = 8
SIMS = {}
# The rate test's margin either side of each limit (see the module docstring).
PENNY = 0.01


@pytest.fixture(scope="module", autouse=True)
def release_simulations():
    yield
    SIMS.clear()


def sim_for(year):
    if year not in SIMS:
        people, benunits, households = {}, {}, {}
        for i in range(K):
            people[f"r{i}"] = {"age": {year: 40}}
            people[f"d{i}"] = {"age": {year: 40}}
            benunits[f"b{i}"] = {
                "members": [f"r{i}", f"d{i}"],
                "is_married": {year: True},
            }
            households[f"h{i}"] = {
                "members": [f"r{i}", f"d{i}"],
                "region": {year: "LONDON"},
            }
        SIMS[year] = Simulation(
            situation={"people": people, "benunits": benunits, "households": households}
        )
    return SIMS[year]


def scale_tax(thresholds, rates, income):
    tax = np.zeros_like(income)
    bounds = list(thresholds) + [np.inf]
    for i, rate in enumerate(rates):
        tax += rate * np.clip(income - bounds[i], 0, bounds[i + 1] - bounds[i])
    return tax


def banded(lo, hi, B, H, r):
    """Tax at the basic, higher and additional rates ``r`` on income from lo to hi."""

    def seg(a, b):
        return np.maximum(0, np.minimum(hi, b) - np.maximum(lo, a))

    return r[0] * seg(-np.inf, B) + r[1] * seg(B, H) + r[2] * seg(H, np.inf)


class Law:
    def __init__(self, year):
        p = (
            sim_for(year)
            .tax_benefit_system.parameters(f"{year}-06-01")
            .gov.hmrc.income_tax
        )
        rates, allow = p.rates, p.allowances
        self.year = year
        self.other_first = year >= 2027  # FA 2026 s. 6(8)
        self.uk = (list(rates.uk.thresholds), list(rates.uk.rates))
        self.B, self.H = rates.uk.thresholds[1], rates.uk.thresholds[2]
        self.div = (list(rates.dividends.thresholds), list(rates.dividends.rates))
        self.sav = (rates.savings.basic, rates.savings.higher, rates.savings.additional)
        self.prop = (
            rates.property.basic,
            rates.property.higher,
            rates.property.additional,
        )
        self.L = rates.savings_starter_rate.allowance
        self.psa = allow.personal_savings_allowance
        self.DA = allow.dividend_allowance
        self.PA0 = allow.personal_allowance.amount
        # s. 55B(3)-(5): basic rate of 10% of the s. 35(1) amount, rounded up to £10.
        self.ma = rates.uk.rates[0] * np.ceil(0.1 * self.PA0 / 10) * 10

    def pa(self, n):
        # s. 35(2) takes half the excess off; s. 35(3) rounds what remains up to
        # a whole pound. 1e-6 keeps float64 rounding from adding a pound.
        tapered = self.PA0 - np.maximum(0, n - 100_000) / 2
        return np.maximum(0, np.ceil(tapered - 1e-6))

    def liability(self, pay, prop, sav, div, to_s, to_v, margin=0.0, e=1e-6):
        """Step 5 tax, rate-test result with every limit moved by ``margin``,
        and feasibility, for each share (arrays broadcast). ``e`` covers float64
        rounding on the grid's shares and float32 rounding of the model's."""
        n = pay + prop + sav + div
        d = np.minimum(self.pa(n), n)
        if self.other_first:  # s. 25(3A): other income first
            to_other = np.minimum(pay, d)
            to_p = d - to_other - to_s - to_v
            O, P = pay - to_other, prop - to_p
            feasible = (to_p >= -e) & (to_p <= prop + e)
        else:
            to_ns = d - to_s - to_v
            O, P = pay + prop - to_ns, 0 * pay
            feasible = (to_ns >= -e) & (to_ns <= pay + prop + e)
        feasible &= (to_s >= -e) & (to_s <= sav + e) & (to_v >= -e) & (to_v <= div + e)
        S, V = sav - to_s, div - to_v
        X = O + P
        T = n - d
        B, H = self.B, self.H
        psa = np.where(
            T > H, self.psa.additional, np.where(T > B, self.psa.higher, self.psa.basic)
        )
        tax = scale_tax(*self.uk, O) + banded(O, X, B, H, self.prop)
        Z = np.minimum(X + S, np.maximum(X, self.L) + psa)  # ss. 12, 12A
        tax += banded(Z, X + S, B, H, self.sav)
        top_nil = X + S + np.minimum(self.DA, V)  # s. 13A
        tax += scale_tax(*self.div, X + S + V) - scale_tax(*self.div, top_nil)
        limit = B + margin
        meets = (
            (X <= limit)
            & ~((X + S > limit) & (X + S > Z + e))
            & ~((V > e) & (X + S + V > limit))
        )
        return tax, meets, feasible

    def least(self, pay, prop, sav, div, to_s, to_v, margin):
        """The least liability over the shares given, with the rate test's limits
        moved by ``margin``."""
        tax, meets, ok = self.liability(pay, prop, sav, div, to_s, to_v, margin)
        liability = np.maximum(0, tax - self.ma * meets)
        return np.where(ok, liability, np.inf), liability


def money(hi):
    return st.integers(0, int(hi * 100)).map(lambda c: c / 100)


amount = st.one_of(
    st.just(0.0),
    money(20_000),
    money(80_000),
    st.sampled_from([500.0, 1_000.0, 1_570.0, 5_000.0, 9_000.0, 12_570.0]),
)
offset = st.one_of(
    st.sampled_from([0.0, -0.01, -0.02, -0.05, 0.01, -0.5]),
    money(600).map(lambda v: v - 300),
)
independent = st.tuples(st.just("free"), amount, amount, amount, amount)
near_limit = st.tuples(st.just("near"), offset, amount, amount, amount)
rows = st.lists(st.one_of(independent, near_limit), min_size=K, max_size=K)


def incomes(year, row):
    kind, a, sav, div, prop = row
    prop = prop if year >= 2027 else 0.0
    if kind == "near":  # Step 3 income near the basic rate limit plus £500
        pay = max(0.0, round(37_700 + 12_570 + 500 + a - sav - div - prop, 2))
    else:
        pay = a
    return pay, prop, sav, div


def check(year, drawn):
    law = Law(year)
    data = np.array([incomes(year, row) for row in drawn], dtype=float)
    pay, prop, sav, div = data.T
    sim = sim_for(year)
    for name, values in zip(
        [
            "employment_income",
            "property_income",
            "savings_interest_income",
            "dividend_income",
        ],
        [pay, prop, sav, div],
    ):
        full = np.zeros(2 * K)
        full[0::2] = values
        sim.set_input(name, year, full)
    sim.set_input("uses_property_allowance", year, np.zeros(2 * K, dtype=bool))
    sim.reset_calculations()

    def calc(v):
        return np.asarray(sim.calculate(v, year), dtype=float)[0::2]

    model_tax = calc("income_tax")
    granted = calc("marriage_allowance_tax_reduction") > 0
    m_s, m_v = (
        calc("received_allowances_savings_income"),
        calc("received_allowances_dividend_income"),
    )
    n = pay + prop + sav + div
    assert np.allclose(calc("allowances"), np.minimum(law.pa(n), 1e12), atol=0.02)
    tol = 0.02 + 1e-6 * n
    # 1. At the model's own share: the Step 5 tax, and the reduction wherever
    # the strict test passes and there is tax to reduce, and nowhere the loose
    # test fails. marriage_allowance_tax_reduction never exceeds the tax left,
    # so a person with no Step 5 tax gets none.
    step_5, strict, ok = law.liability(pay, prop, sav, div, m_s, m_v, -PENNY, 0.005)
    _, loose, _ = law.liability(pay, prop, sav, div, m_s, m_v, PENNY, 0.005)
    assert np.all(ok), "model share infeasible"
    at_share = np.maximum(0, step_5 - law.ma * granted)
    bad = (
        (np.abs(model_tax - at_share) > tol)
        | (strict & ~granted & (step_5 > tol))
        | (granted & ~loose)
    )
    assert not bad.any(), [
        (data[i].tolist(), model_tax[i], at_share[i], granted[i], strict[i], loose[i])
        for i in np.flatnonzero(bad)
    ]
    # 2. No share on the grid, the thin sets or the old order leaves less liability.
    d = np.minimum(law.pa(n), n)
    shared = d - np.minimum(pay, d) if law.other_first else d
    f = np.linspace(0, 1, 41)
    psa = np.where(
        n - d > law.H,
        law.psa.additional,
        np.where(n - d > law.B, law.psa.higher, law.psa.basic),
    )
    s_opts = np.column_stack(
        [
            np.minimum(sav, shared)[:, None] * f,
            np.maximum(0, sav - psa),
            np.maximum(0, sav - psa - 0.01),
            np.minimum(sav, shared),
        ]
    )
    v_opts = np.column_stack(
        [np.minimum(div, shared)[:, None] * f, div, np.minimum(div, shared)]
    )
    to_s = np.repeat(s_opts, v_opts.shape[1], axis=1)
    to_v = np.tile(v_opts, s_opts.shape[1])
    # Old order (non-savings, savings, dividends), and the shares leaving
    # non-savings income at the basic rate limit, and a penny under it, with no
    # dividends.
    first = (pay + prop) if not law.other_first else prop
    old_s = np.minimum(sav, np.maximum(0, shared - first))
    old_v = np.minimum(div, np.maximum(0, shared - first - old_s))
    corner_v = np.minimum(div, shared)
    corners = [
        np.clip(
            shared
            - corner_v
            - np.maximum(
                0,
                first
                - np.where(law.other_first, limit - np.maximum(0, pay - d), limit),
            ),
            0,
            sav,
        )
        for limit in (law.B, law.B - PENNY)
    ]
    to_s = np.column_stack([to_s, old_s, *corners])
    to_v = np.column_stack([to_v, old_v, corner_v, corner_v])

    def col(a):
        return a[:, None]

    shares = (col(pay), col(prop), col(sav), col(div), to_s, to_v)
    strict_options, strict_liability = law.least(*shares, -PENNY)
    strict_least = strict_options.min(axis=1)
    old = strict_liability[:, -3]
    # The grid holds the least liability only approximately, so it bounds the
    # model's tax from above. Check 1 bounds it from below: the model's tax is
    # the law's liability at a share the model can hold, with the reduction only
    # where the loose test passes.
    worse = (model_tax > strict_least + tol) | (model_tax > old + tol)
    assert not worse.any(), [
        dict(
            incomes=data[i].tolist(),
            model=model_tax[i],
            strict_least=strict_least[i],
            old=old[i],
        )
        for i in np.flatnonzero(worse)
    ]


SETTINGS = settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    suppress_health_check=list(HealthCheck),
)


@SETTINGS
@given(st.sampled_from([2026, 2027]), rows)
@example(2026, [("free", 40_200.0, 9_000.0, 1_570.0, 0.0)] * K)
@example(2026, [("free", 50_000.0, 500.0, 270.0, 0.0)] * K)
@example(2026, [("free", 50_269.99, 500.0, 0.01, 0.0)] * K)
def test_model_tax_is_the_least_liability_the_law_allows(year, drawn):
    check(year, drawn)
