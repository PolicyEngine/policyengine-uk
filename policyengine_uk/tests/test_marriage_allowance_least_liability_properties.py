"""The least liability under the Marriage Allowance rate test, against the law.

A married recipient in London whose partner has no income. The oracle works
the law itself (ITA 2007 ss. 10-13A, 12B, 16, 23, 25(2)/(3A), 55B), reading only
rate and allowance values from the parameter tree. For every drawn recipient:

1. the model's income tax equals the oracle's liability at the model's own share;
2. the model's income tax never exceeds the oracle's liability under the old
   order or any share on a grid (plus the thin sets where the rate test holds),
   each with the Marriage Allowance reduction that share wins.

The oracle applies the rate test at the statutory limits, as s. 55B(2) does,
so a share that leaves non-savings income at the basic rate limit meets it.
The explicit examples are recipients for whom only such a share qualifies.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

K = 8
SIMS = {}


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
        return np.maximum(0, self.PA0 - np.maximum(0, n - 100_000) / 2)  # s. 35(2)

    def liability(self, pay, prop, sav, div, to_s, to_v, e=1e-6):
        """Liability and rate-test result for each share (arrays broadcast)."""
        n = pay + prop + sav + div
        # ``e`` covers float64 rounding on the grid's shares; at the model's own
        # share, held in float32, the caller passes half a penny.
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
        meets = (
            (X <= B + e)
            & ~((X + S > B + e) & (X + S > Z + e))
            & ~((V > e) & (X + S + V > B + e))
        )
        return np.maximum(0, tax - self.ma * meets), meets, feasible


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
    m_s, m_v = (
        calc("received_allowances_savings_income"),
        calc("received_allowances_dividend_income"),
    )
    n = pay + prop + sav + div
    assert np.allclose(calc("allowances"), np.minimum(law.pa(n), 1e12), atol=0.02)
    tol = 0.02 + 1e-6 * n
    # 1. The model's tax is the law's liability at the model's own share.
    at_share, _, ok = law.liability(pay, prop, sav, div, m_s, m_v, e=0.005)
    assert np.all(ok), "model share infeasible"
    bad = np.abs(model_tax - at_share) > tol
    assert not bad.any(), [
        (data[i].tolist(), model_tax[i], at_share[i]) for i in np.flatnonzero(bad)
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
    # Old order (non-savings, savings, dividends) and the share leaving
    # non-savings income at the basic rate limit with no dividends.
    first = (pay + prop) if not law.other_first else prop
    old_s = np.minimum(sav, np.maximum(0, shared - first))
    old_v = np.minimum(div, np.maximum(0, shared - first - old_s))
    corner_v = np.minimum(div, shared)
    corner_s = np.clip(
        shared
        - corner_v
        - np.maximum(
            0, first - np.where(law.other_first, law.B - np.maximum(0, pay - d), law.B)
        ),
        0,
        sav,
    )
    to_s = np.column_stack([to_s, old_s, corner_s])
    to_v = np.column_stack([to_v, old_v, corner_v])

    def col(a):
        return a[:, None]

    liab, meets, ok = law.liability(col(pay), col(prop), col(sav), col(div), to_s, to_v)
    best = np.where(ok, liab, np.inf).min(axis=1)
    old = liab[:, -2]
    worse = (model_tax > best + tol) | (model_tax > old + tol)
    assert not worse.any(), [
        dict(
            incomes=data[i].tolist(),
            model=model_tax[i],
            least=best[i],
            old=old[i],
            share=(
                to_s[i, np.argmin(np.where(ok[i], liab[i], np.inf))],
                to_v[i, np.argmin(np.where(ok[i], liab[i], np.inf))],
            ),
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
