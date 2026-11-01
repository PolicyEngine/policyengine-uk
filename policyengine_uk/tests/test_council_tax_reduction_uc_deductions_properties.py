"""Four councils count the Universal Credit award before debt deductions (#2799).

Merton and Kingston upon Thames count "the amount of the award of universal
credit" in their 2026-27 schemes, which reproduce SI 2012/2886 Sch para
37(3)(a) and (4). Newham counts "the amount of entitlement to universal
credit", and Westminster's summary compares the maximum amount "to the actual
universal credit award plus any other income and earnings received".
Parliament sets the award as the maximum amount less the income amounts
(Welfare Reform Act 2012 s 8(1)), and the Secretary of State reduces it for the
benefit cap (UC Regs 2013 reg 81(1)). The Secretary of State then pays part of
it to third parties for the claimant's debts (SI 2013/380 Sch 6 para 2(1)),
leaving at least a penny payable (para 3(1)(a)).

Invariants, in 2026, for working-age single people, couples and families with
children in the four councils, across benefit cap reductions from nil to more
than the award, and deduction demands from nil through the 15% cap to an
above-cap excess:

1. Award recovery: universal_credit + uc_deductions equals the award after the
   cap, max(universal_credit_pre_benefit_cap - uc_benefit_cap_reduction, 0),
   and a family with deductions keeps at least a penny a month payable.
2. Deduction invariance: while the award exceeds nil, each council's reduction
   stays the same with and without the deductions.
3. Differential: where the award exceeds nil, the reduction equals a reference
   that the test writes from para 37 and each scheme's rates: max(0, liability
   x maximum support rate - withdrawal rate x max(0, earned income + unearned
   income + award - maximum amount)).

Each example sets its inputs on one simulation that the module builds once.
It holds a pair of households for each family, one with deductions and one
without.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, event, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PENNY_A_MONTH = 0.01 * 12
# Maximum support rate and weekly withdrawal rate of each 2026-27 scheme:
# Merton and Kingston upon Thames take 2 6/7% a day, Newham 3 4/7% a day of
# the excess income on 70% of the liability, and Westminster 20%.
SCHEMES = {
    "MERTON": (1.0, 0.20),
    "KINGSTON_UPON_THAMES": (1.0, 0.20),
    "NEWHAM": (0.70, 0.25),
    "WESTMINSTER": (1.0, 0.20),
}
COUNCIL_REDUCTIONS = [
    "merton_council_tax_reduction",
    "kingston_upon_thames_council_tax_reduction",
    "newham_council_tax_reduction",
    "westminster_council_tax_reduction",
]
# Adults and children in each family, so the pairs cover single people,
# couples and families with a work allowance.
STRUCTURES = [(1, 0), (2, 0), (1, 1), (2, 2)] * 2
COMBINATIONS = [
    "ADVANCE_ONLY",
    "THIRD_PARTY_ONLY",
    "GOVERNMENT_ONLY",
    "ADVANCE_AND_GOVERNMENT",
    "ADVANCE_AND_THIRD_PARTY",
    "THIRD_PARTY_AND_GOVERNMENT",
    "ALL_THREE",
]
BENUNIT_OUTPUTS = [
    "universal_credit",
    "uc_deductions",
    "uc_deduction_rate",
    "universal_credit_pre_benefit_cap",
    "uc_benefit_cap_reduction",
    "uc_maximum_amount",
    "uc_earned_income_before_work_allowance",
    "uc_unearned_income",
    "simulated_council_tax_reduction_benunit",
    *COUNCIL_REDUCTIONS,
]
PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def situation():
    """Two households for each family in STRUCTURES, each its own benefit
    unit: slot 2k has no deductions, slot 2k + 1 the drawn ones."""
    people, benunits, households = {}, {}, {}
    for k, (adults, children) in enumerate(STRUCTURES):
        for slot in (2 * k, 2 * k + 1):
            names = []
            for j in range(adults):
                name = f"a{slot}_{j}"
                people[name] = {
                    "age": {YEAR: 35 - 2 * j},
                    "is_claimant_or_partner": {YEAR: True},
                    "employment_income": {YEAR: 0.0},
                }
                names.append(name)
            for j in range(children):
                name = f"c{slot}_{j}"
                people[name] = {
                    "age": {YEAR: 5 + 3 * j},
                    "is_claimant_or_partner": {YEAR: False},
                }
                names.append(name)
            benunits[f"b{slot}"] = {
                "members": names,
                "would_claim_uc": {YEAR: True},
                "claims_all_entitled_benefits": {YEAR: True},
                "uc_benefit_cap_reduction": {YEAR: 0.0},
                "uc_has_deduction": {YEAR: False},
                "uc_latent_deduction_rate": {YEAR: 0.0},
                "uc_deduction_combination": {YEAR: "NONE"},
            }
            households[f"h{slot}"] = {
                "members": names,
                "country": {YEAR: "ENGLAND"},
                "region": {YEAR: "LONDON"},
                "local_authority": {YEAR: "MERTON"},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "rent": {YEAR: 0.0},
                "council_tax": {YEAR: 2_000.0},
                "savings": {YEAR: 0.0},
            }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def simulation(cloned_uk_tax_benefit_system):
    return Simulation(situation=situation())


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


@st.composite
def family(draw):
    return dict(
        council=draw(st.sampled_from(sorted(SCHEMES))),
        earnings=[draw(st.one_of(st.just(0.0), money(30_000))) for _ in range(2)],
        rent=draw(st.one_of(st.just(0.0), money(15_000))),
        council_tax=draw(st.floats(500, 4_000)),
        # From nil to more than any award the draws give, so the cap can
        # take the whole award.
        cap_reduction=draw(st.one_of(st.just(0.0), money(30_000))),
        # Latent demand as a share of the standard allowance: from nil
        # through the 15% cap, and above the 25% calibration cap, where the
        # excess sits on top of the cap.
        latent_rate=draw(
            st.one_of(st.sampled_from([0.05, 0.15, 0.25, 0.30, 0.40]), money(0.40))
        ),
        combination=draw(st.sampled_from(COMBINATIONS)),
    )


families = st.lists(family(), min_size=len(STRUCTURES), max_size=len(STRUCTURES))

# The issue's example (#2799): a single person earning 8,000, renting from the
# council at 7,800, with council tax of 2,600.
ISSUE = dict(
    council="MERTON",
    earnings=[8_000.0, 0.0],
    rent=7_800.0,
    council_tax=2_600.0,
    cap_reduction=0.0,
    latent_rate=0.15,
    combination="THIRD_PARTY_ONLY",
)
EXPLICIT = [
    ISSUE,
    # A couple whose award the cap reduces and whose deductions include an
    # above-cap excess.
    {**ISSUE, "council": "NEWHAM", "cap_reduction": 1_500.0, "latent_rate": 0.30},
    {**ISSUE, "council": "KINGSTON_UPON_THAMES", "combination": "ALL_THREE"},
    # The cap takes the whole award.
    {**ISSUE, "council": "WESTMINSTER", "cap_reduction": 30_000.0},
    {**ISSUE, "council": "WESTMINSTER", "earnings": [12_000.0, 0.0]},
    {**ISSUE, "council": "NEWHAM", "latent_rate": 0.40},
    {**ISSUE, "council": "MERTON", "rent": 0.0, "earnings": [0.0, 0.0]},
    {**ISSUE, "council": "KINGSTON_UPON_THAMES", "cap_reduction": 4_000.0},
]


def pairs(values):
    """One value for each household of each family's pair."""
    return np.repeat(np.asarray(values), 2)


def calculate(simulation, fams):
    """Set each family's inputs on its pair of households and calculate."""
    # situation() puts family k // 2 in benefit unit k.
    benunit_of = simulation.populations["benunit"].members_entity_id
    adult = np.asarray(simulation.calculate("is_claimant_or_partner", YEAR))
    earnings = np.zeros(len(benunit_of))
    adults_seen = np.zeros(2 * len(fams), dtype=int)
    for i in np.flatnonzero(adult):
        b = benunit_of[i]
        earnings[i] = fams[b // 2]["earnings"][adults_seen[b]]
        adults_seen[b] += 1
    with_deductions = np.arange(2 * len(fams)) % 2 == 1
    inputs = {
        # Simulation moves employment_income here as it builds.
        "employment_income_before_lsr": earnings,
        "local_authority": pairs([f["council"] for f in fams]),
        "rent": pairs([f["rent"] for f in fams]),
        "council_tax": pairs([f["council_tax"] for f in fams]),
        "uc_benefit_cap_reduction": pairs([f["cap_reduction"] for f in fams]),
        "uc_has_deduction": with_deductions,
        "uc_latent_deduction_rate": np.where(
            with_deductions, pairs([f["latent_rate"] for f in fams]), 0.0
        ),
        "uc_deduction_combination": np.where(
            with_deductions, pairs([f["combination"] for f in fams]), "NONE"
        ),
    }
    for name, value in inputs.items():
        variable = simulation.tax_benefit_system.variables[name]
        possible_values = getattr(variable, "possible_values", None)
        if possible_values is not None:
            value = possible_values.encode(np.asarray(value))
        simulation.set_input(name, YEAR, value)
    values = {v: np.asarray(simulation.calculate(v, YEAR)) for v in BENUNIT_OUTPUTS}
    values["liability"] = np.asarray(
        simulation.calculate("council_tax_reduction_maximum_eligible_liability", YEAR)
    )
    return values


def award_after_cap(v):
    return np.maximum(
        v["universal_credit_pre_benefit_cap"] - v["uc_benefit_cap_reduction"], 0
    )


@PROPERTY_SETTINGS
@given(fams=families)
@example(fams=EXPLICIT)
def test_four_councils_count_the_universal_credit_award_before_deductions(
    simulation, fams
):
    v = calculate(simulation, fams)
    uc, deductions = v["universal_credit"], v["uc_deductions"]
    award = award_after_cap(v)
    base, plus = slice(0, None, 2), slice(1, None, 2)

    # 1. The award and the amount payable.
    assert np.allclose(uc + deductions, award, atol=0.01), [
        (fams[k // 2], uc[k], deductions[k], award[k])
        for k in np.flatnonzero(~np.isclose(uc + deductions, award, atol=0.01))[:3]
    ]
    assert np.all(deductions[base] == 0)
    taken = deductions > 0
    # The model holds amounts in float32, so allow a penny of rounding.
    assert np.all(uc[taken] >= PENNY_A_MONTH - 0.01)

    # 2. The reductions do not move with the deductions while the award
    # exceeds nil.
    council = sum(v[name] for name in COUNCIL_REDUCTIONS)
    assert np.allclose(council, v["simulated_council_tax_reduction_benunit"])
    has_award = (award[base] > 0) & (award[plus] > 0)
    for k in np.flatnonzero(has_award):
        event(f"{fams[k]['council']}: deductions {deductions[2 * k + 1] > 0}")
    assert np.allclose(council[plus][has_award], council[base][has_award], atol=0.01), [
        (fams[k], council[2 * k], council[2 * k + 1], deductions[2 * k + 1])
        for k in np.flatnonzero(
            has_award & ~np.isclose(council[plus], council[base], atol=0.01)
        )[:3]
    ]

    # 3. Differential against the scheme's own arithmetic.
    rates = np.array([SCHEMES[f["council"]] for f in fams]).repeat(2, axis=0)
    excess = np.maximum(
        v["uc_earned_income_before_work_allowance"]
        + v["uc_unearned_income"]
        + award
        - v["uc_maximum_amount"],
        0,
    )
    reference = np.maximum(v["liability"] * rates[:, 0] - rates[:, 1] * excess, 0)
    on_uc = award > 0
    assert np.allclose(council[on_uc], reference[on_uc], atol=0.01), [
        (fams[k // 2], council[k], reference[k])
        for k in np.flatnonzero(on_uc & ~np.isclose(council, reference, atol=0.01))[:3]
    ]

    if fams == EXPLICIT:
        # Not vacuous: the issue's case takes 764.82 at the cap and gives a
        # partial reduction of 1,880 either way; the Newham couple's rate is
        # the 15% cap plus a 5% excess; the cap takes the fourth family's
        # whole award; and every other family keeps an award and repays debt.
        assert np.isclose(deductions[1], 764.82, atol=0.01)
        assert np.allclose(council[:2], 1_880, atol=0.01)
        assert np.isclose(v["uc_deduction_rate"][3], 0.20)
        assert np.all(award[6:8] == 0)
        assert np.all(deductions[plus][has_award] > 0)
        assert has_award.sum() == len(EXPLICIT) - 1
