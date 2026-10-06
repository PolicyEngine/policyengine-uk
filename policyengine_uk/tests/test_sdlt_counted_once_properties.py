"""Property-based tests: Stamp Duty Land Tax enters the tax totals once.

SDLT reaches a household in two parts. ``expected_sdlt`` is the SDLT on the
household's own purchases and leases (``stamp_duty_land_tax``), and
``corporate_sdlt`` is its share, through ``shareholding``, of the SDLT that
corporations pay. ``household_tax``, ``gov_tax`` and
``pre_budget_change_household_tax`` each list both parts, so each part must
appear in them exactly once, and ``gov.hmrc.stamp_duty.abolish`` must remove
both.

Each example builds a two-household population and simulates it three ways:

- B: the baseline;
- A: with ``gov.hmrc.stamp_duty.abolish`` set;
- Z: the baseline with both corporate SDLT revenue statistics set to zero.

The population varies the year, each household's region (inside and outside
England and Northern Ireland), purchases of main, additional and
non-residential property (or none), first-home status, earnings, corporate
wealth (zero or positive in either household) and positive weights. "Equal"
below means equal up to the float32 rounding of the totals (32 float32 ulps
of the largest value compared, per household); "exactly" means bit-equal.

1. Own SDLT: ``expected_sdlt`` in B is exactly ``stamp_duty_land_tax``, so a
   household with no purchase, or outside England and Northern Ireland, has
   none.
2. Corporate SDLT once: for each total T, T(B) - T(Z) equals
   ``corporate_sdlt`` in B. Counting it twice would make the gap twice that.
3. Abolition removes all of it once: T(B) - T(A) equals
   ``stamp_duty_land_tax`` + ``corporate_sdlt`` in B, and T(Z) - T(A) equals
   ``stamp_duty_land_tax`` in B, so no corporate SDLT is left after abolition.
4. Abolition zeroes both parts: ``expected_sdlt`` and ``corporate_sdlt`` are
   exactly 0 in A, ``corporate_tax_incidence`` in A equals ``business_rates``,
   and ``corporate_tax_incidence`` falls by ``corporate_sdlt`` in B.
5. Weighted totals: when some household has corporate-sector wealth, the
   weighted sum of ``corporate_sdlt`` in B is the corporate SDLT revenue
   statistic (within a relative 1e-6), and weighted ``gov_tax`` falls under
   abolition by weighted ``stamp_duty_land_tax`` plus that revenue, once.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

ALWAYS = "2000-01-01.2100-12-31"
ABOLISH_SDLT = {"gov.hmrc.stamp_duty.abolish": {ALWAYS: True}}
NO_CORPORATE_SDLT = {
    "gov.hmrc.stamp_duty.statistics.residential.corporate.revenue": {ALWAYS: 0},
    "gov.hmrc.stamp_duty.statistics.non_residential.corporate.revenue": {ALWAYS: 0},
}
TOTALS = ["household_tax", "gov_tax", "pre_budget_change_household_tax"]
VARIABLES = TOTALS + [
    "stamp_duty_land_tax",
    "expected_sdlt",
    "corporate_sdlt",
    "corporate_tax_incidence",
    "business_rates",
    "corporate_sector_wealth",
    "household_weight",
]
REGIONS = ["LONDON", "NORTH_WEST", "NORTHERN_IRELAND", "SCOTLAND", "WALES"]
ULPS = 32

purchase = st.one_of(st.just(0.0), st.floats(40_000, 5_000_000))

household = st.fixed_dictionaries(
    {
        "region": st.sampled_from(REGIONS),
        "main_residential_property_purchased": purchase,
        "main_residential_property_purchased_is_first_home": st.booleans(),
        "additional_residential_property_purchased": purchase,
        "non_residential_property_purchased": purchase,
        "corporate_wealth": st.one_of(st.just(0.0), st.floats(1_000, 10_000_000)),
        "household_weight": st.floats(1, 10_000),
        "employment_income": st.floats(0, 200_000),
    }
)


def situation(households: list, year: int) -> dict:
    people, benunits, hh = {}, {}, {}
    for i, inputs in enumerate(households):
        person, benunit = f"person_{i}", f"benunit_{i}"
        people[person] = {
            "age": {year: 40 + 20 * i},
            "employment_income": {year: inputs["employment_income"]},
        }
        benunits[benunit] = {"members": [person]}
        hh[f"household_{i}"] = {
            "members": [person],
            **{
                name: {year: value}
                for name, value in inputs.items()
                if name != "employment_income"
            },
        }
    return {"people": people, "benunits": benunits, "households": hh}


def simulate(households: list, year: int, reform=None) -> dict:
    sim = Simulation(situation=situation(households, year), reform=reform)
    return {
        name: np.asarray(sim.calculate(name, year), dtype=np.float64)
        for name in VARIABLES
    }


def tolerance(*arrays) -> np.ndarray:
    """Per-household rounding allowance for float32 totals."""
    magnitude = np.max(np.abs(np.stack(arrays)), axis=0)
    return ULPS * np.spacing(magnitude.astype(np.float32)).astype(np.float64)


def corporate_sdlt_revenue(year: int) -> float:
    statistics = system.parameters(str(year)).gov.hmrc.stamp_duty.statistics
    return float(
        statistics.residential.corporate.revenue
        + statistics.non_residential.corporate.revenue
    )


@settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    households=st.lists(household, min_size=2, max_size=2),
    year=st.sampled_from([2024, 2025, 2026, 2027]),
)
def test_sdlt_is_counted_once_and_abolition_removes_it(households, year):
    b = simulate(households, year)
    a = simulate(households, year, ABOLISH_SDLT)
    z = simulate(households, year, NO_CORPORATE_SDLT)

    sdlt = b["stamp_duty_land_tax"]
    corporate = b["corporate_sdlt"]

    # 1. Own SDLT, with nothing added.
    np.testing.assert_array_equal(b["expected_sdlt"], sdlt)

    for total in TOTALS:
        # 2. Corporate SDLT is in the baseline total once.
        np.testing.assert_array_less(
            np.abs(b[total] - z[total] - corporate),
            tolerance(b[total], z[total], corporate) + 1e-9,
            err_msg=f"{total}: corporate SDLT not counted exactly once",
        )
        # 3. Abolition removes household and corporate SDLT, once.
        np.testing.assert_array_less(
            np.abs(b[total] - a[total] - (sdlt + corporate)),
            tolerance(b[total], a[total], sdlt + corporate) + 1e-9,
            err_msg=f"{total}: abolition did not remove all SDLT once",
        )
        np.testing.assert_array_less(
            np.abs(z[total] - a[total] - sdlt),
            tolerance(z[total], a[total], sdlt) + 1e-9,
            err_msg=f"{total}: corporate SDLT left after abolition",
        )

    # 4. Abolition zeroes both parts and the corporate incidence they feed.
    np.testing.assert_array_equal(a["expected_sdlt"], 0)
    np.testing.assert_array_equal(a["corporate_sdlt"], 0)
    np.testing.assert_array_equal(a["corporate_tax_incidence"], a["business_rates"])
    np.testing.assert_array_less(
        np.abs(b["corporate_tax_incidence"] - a["corporate_tax_incidence"] - corporate),
        tolerance(b["corporate_tax_incidence"], corporate) + 1e-9,
    )

    # 5. Weighted, the corporate part is the revenue statistic, once.
    weight = b["household_weight"]
    if (b["corporate_sector_wealth"] * weight).sum() > 0:
        revenue = corporate_sdlt_revenue(year)
        assert np.isclose((corporate * weight).sum(), revenue, rtol=1e-6, atol=0)
        removed = ((b["gov_tax"] - a["gov_tax"]) * weight).sum()
        allowance = (tolerance(b["gov_tax"], a["gov_tax"]) * weight).sum()
        assert abs(removed - ((sdlt * weight).sum() + revenue)) <= allowance + (
            1e-6 * revenue
        )
    else:
        np.testing.assert_array_equal(corporate, 0)
