"""A pensioner's Council Tax Reduction child amounts and tariff income.

The pensioner schemes add an amount for each child or young person in the
family and, in Wales, a family premium (SI 2012/2885 Sch 1 para 6(1)(b)-(c)
and Sch 2 paras 2-3; WSI 2013/3029 Sch 1 para 1(1)(b)-(c) and Sch 2 paras
2-3; SSI 2012/319 reg 20(b) and Sch 1 para 3). England counted at most two
from 2018-19 to 2024-25 unless a Child Tax Credit award included more (SI
2017/1305 reg 7; SI 2025/39 reg 5(2)). A pensioner's capital counts as a
weekly income of £1 for each £500, or part of £500, over £10,000 (SI
2012/2885 Sch 1 para 37; WSI 2013/3029 Sch 1 para 31; SSI 2012/319 reg
27(2)), up to the £16,000 capital limit, except where Pension Credit sets the
means test.

Invariants:

1. Tariff income is 52 times £1 for each £500, or part of £500, of capital
   above £10,000 and up to £16,000, for a pensioner off Pension Credit, and
   it never falls as capital rises. Capital changes nothing else in the
   applicable income, and the award never rises with capital.
2. Adding a dependent child never lowers the applicable amount. For a
   pensioner it adds the scheme's weekly amount for 52 weeks, unless England's
   2018-19 to 2024-25 limit is already reached, and in Wales the family
   premium with the first child.
3. A pensioner with no child and capital up to £10,000, and every working-age
   family, gets no child amount, family premium or tariff income, so their
   applicable amount, applicable income and award are origin/main's.
   test_matches_origin_main_on_unchanged_households checks that against
   values computed on origin/main.
"""

import math

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

AUTHORITIES = {"ENGLAND": "MAIDSTONE", "SCOTLAND": "GLASGOW_CITY", "WALES": "CARDIFF"}
# Weekly child or young person amounts and family premiums, from the
# parameter files' sources.
CHILD_AMOUNT = {
    ("ENGLAND", 2019): 66.90,
    ("ENGLAND", 2021): 68.60,
    ("ENGLAND", 2024): 83.24,
    ("ENGLAND", 2025): 84.66,
    ("ENGLAND", 2026): 87.88,
    ("WALES", 2019): 66.90,
    ("WALES", 2021): 66.90,
    ("WALES", 2024): 83.24,
    ("WALES", 2025): 84.66,
    ("WALES", 2026): 87.88,
    ("SCOTLAND", 2019): 83.63,
    ("SCOTLAND", 2021): 85.75,
    ("SCOTLAND", 2024): 104.05,
    ("SCOTLAND", 2025): 105.85,
    ("SCOTLAND", 2026): 109.85,
}
WELSH_FAMILY_PREMIUM = {2019: 17.45, 2021: 17.45, 2024: 19.15, 2025: 19.48, 2026: 20.22}
YEARS = (2019, 2021, 2024, 2025, 2026)
OUTPUTS = (
    "council_tax_reduction_pensioner",
    "council_tax_reduction_applicable_amount",
    "council_tax_reduction_applicable_income",
    "council_tax_reduction_pensioner_child_amounts",
    "council_tax_reduction_pensioner_family_premium",
    "council_tax_reduction_pensioner_tariff_income",
    "council_tax_benefit",
)
SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def situation(households, year):
    """One benefit unit and household for each spec, in one simulation."""
    data = {"people": {}, "benunits": {}, "households": {}}
    for index, spec in enumerate(households):
        members = []
        adults = [spec["age"]]
        if spec.get("partner_age") is not None:
            adults.append(spec["partner_age"])
        for number, age in enumerate(adults):
            name = f"adult_{index}_{number}"
            income = "state_pension" if age >= 67 else "employment_income"
            data["people"][name] = {
                "age": {year: age},
                income: {year: spec["income"] if number == 0 else 0},
            }
            members.append(name)
        for number, age in enumerate(spec.get("children", ())):
            name = f"child_{index}_{number}"
            data["people"][name] = {"age": {year: age}}
            members.append(name)
        data["benunits"][f"family_{index}"] = {
            "members": members,
            "would_claim_pc": {year: spec.get("claims_pc", False)},
            "would_claim_uc": {year: False},
        }
        data["households"][f"home_{index}"] = {
            "members": members,
            "country": {year: spec["country"]},
            "local_authority": {
                year: spec.get("local_authority") or AUTHORITIES[spec["country"]]
            },
            "tenure_type": {year: "OWNED_OUTRIGHT"},
            "council_tax": {year: 2_000},
            "savings": {year: spec["savings"]},
        }
    return data


def calculate(households, year, names=OUTPUTS):
    simulation = Simulation(situation=situation(households, year))
    return {name: np.asarray(simulation.calculate(name, year)) for name in names}


def tariff(capital):
    excess = max(0, min(capital, 16_000) - 10_000)
    return 52 * math.ceil(excess / 500)


countries = st.sampled_from(sorted(AUTHORITIES))
pensioner = st.fixed_dictionaries(
    {
        "country": countries,
        "age": st.integers(70, 95),
        "partner_age": st.one_of(st.none(), st.integers(68, 95)),
        "children": st.lists(st.integers(0, 15), max_size=3),
        "income": st.integers(0, 30_000),
        "savings": st.integers(0, 10_000),
    }
)
family = st.fixed_dictionaries(
    {
        "country": countries,
        "age": st.one_of(st.integers(25, 60), st.integers(70, 95)),
        "partner_age": st.one_of(st.none(), st.integers(25, 60), st.integers(70, 95)),
        "children": st.lists(st.integers(0, 15), max_size=3),
        "income": st.integers(0, 30_000),
        "savings": st.integers(0, 20_000),
        "claims_pc": st.booleans(),
    }
)


@SETTINGS
@given(
    base=pensioner,
    capitals=st.lists(st.integers(0, 30_000), min_size=2, max_size=6).map(sorted),
    year=st.sampled_from(YEARS),
)
def test_tariff_income_is_the_tariff_and_never_falls_as_capital_rises(
    base, capitals, year
):
    households = [dict(base, savings=capital) for capital in capitals]
    result = calculate(households, year)
    assert result["council_tax_reduction_pensioner"].all()
    tariffs = result["council_tax_reduction_pensioner_tariff_income"]
    np.testing.assert_allclose(tariffs, [tariff(c) for c in capitals], atol=0.01)
    assert (np.diff(tariffs) >= 0).all()
    # Capital adds the tariff income and nothing else.
    other_income = result["council_tax_reduction_applicable_income"] - tariffs
    np.testing.assert_allclose(other_income, other_income[0], atol=0.01)
    assert (np.diff(result["council_tax_benefit"]) <= 0.01).all()


@SETTINGS
@given(
    households=st.lists(family, min_size=1, max_size=6),
    child_age=st.integers(0, 15),
    year=st.sampled_from(YEARS),
)
def test_adding_a_dependent_child_never_lowers_the_applicable_amount(
    households, child_age, year
):
    with_child = [
        dict(spec, children=[*spec["children"], child_age]) for spec in households
    ]
    before = calculate(households, year)
    after = calculate(with_child, year)
    rise = (
        after["council_tax_reduction_applicable_amount"]
        - before["council_tax_reduction_applicable_amount"]
    )
    assert (rise >= -0.01).all()
    for index, spec in enumerate(households):
        if not before["council_tax_reduction_pensioner"][index]:
            assert after["council_tax_reduction_pensioner_child_amounts"][index] == 0
            continue
        children = len(spec["children"])
        counted = (
            min(children + 1, 2) - min(children, 2)
            if spec["country"] == "ENGLAND" and 2018 <= year <= 2024
            else 1
        )
        expected = 52 * counted * CHILD_AMOUNT[(spec["country"], year)]
        if spec["country"] == "WALES" and children == 0:
            expected += 52 * WELSH_FAMILY_PREMIUM[year]
        added = (
            after["council_tax_reduction_pensioner_child_amounts"][index]
            + after["council_tax_reduction_pensioner_family_premium"][index]
            - before["council_tax_reduction_pensioner_child_amounts"][index]
            - before["council_tax_reduction_pensioner_family_premium"][index]
        )
        assert added == pytest.approx(expected, abs=0.01)


@SETTINGS
@given(households=st.lists(family, min_size=1, max_size=8), year=st.sampled_from(YEARS))
def test_no_new_amounts_without_a_child_or_capital_over_10000_or_at_working_age(
    households, year
):
    result = calculate(households, year)
    pensioner = result["council_tax_reduction_pensioner"]
    for index, spec in enumerate(households):
        child_amounts = result["council_tax_reduction_pensioner_child_amounts"][index]
        premium = result["council_tax_reduction_pensioner_family_premium"][index]
        tariff_income = result["council_tax_reduction_pensioner_tariff_income"][index]
        if not pensioner[index]:
            assert child_amounts == premium == tariff_income == 0
            continue
        if not spec["children"]:
            assert child_amounts == premium == 0
        if spec["savings"] <= 10_000:
            assert tariff_income == 0


def test_northern_ireland_gets_no_new_amounts():
    spec = {
        "country": "NORTHERN_IRELAND",
        "local_authority": "BELFAST",
        "age": 72,
        "children": [10],
        "income": 12_000,
        "savings": 16_000,
    }
    result = calculate([spec], 2026)
    assert result["council_tax_reduction_pensioner_child_amounts"][0] == 0
    assert result["council_tax_reduction_pensioner_family_premium"][0] == 0
    assert result["council_tax_reduction_pensioner_tariff_income"][0] == 0


# Pensioners with no child and capital up to £10,000, and working-age
# families with and without children and capital, in each nation, including
# English working-age families under the five local schemes the model runs.
UNCHANGED_HOUSEHOLDS = [
    spec
    for country in sorted(AUTHORITIES)
    for spec in (
        {"country": country, "age": 72, "income": 12_000, "savings": 0},
        {
            "country": country,
            "age": 80,
            "partner_age": 75,
            "income": 18_000,
            "savings": 10_000,
        },
        {
            "country": country,
            "age": 70,
            "income": 9_000,
            "savings": 9_999,
            "claims_pc": True,
        },
        {
            "country": country,
            "age": 40,
            "children": [7],
            "income": 15_000,
            "savings": 12_000,
        },
        {
            "country": country,
            "age": 35,
            "partner_age": 33,
            "children": [3, 9],
            "income": 25_000,
            "savings": 16_000,
        },
        {"country": country, "age": 25, "income": 9_000, "savings": 8_000},
    )
] + [
    {
        "country": "ENGLAND",
        "local_authority": authority,
        "age": 40,
        "children": [7],
        "income": 12_000,
        "savings": 14_000,
    }
    for authority in (
        "MERTON",
        "KINGSTON_UPON_THAMES",
        "NEWHAM",
        "WESTMINSTER",
        "OXFORD",
    )
]
DIFFERENTIAL_OUTPUTS = (
    "council_tax_reduction_applicable_amount",
    "council_tax_reduction_applicable_income",
    "council_tax_benefit",
)
# Computed on origin/main at 2da212abc for UNCHANGED_HOUSEHOLDS, in order:
# applicable amount, applicable income and council_tax_benefit.
ORIGIN_MAIN = {
    2019: [
        (9_412, 12_000, 1_482.4),
        (14_071.2, 17_150, 1_384.24),
        (9_412, 9_592.34, 1_963.93),
        (3_801.2, 14_812.24, 0),
        (5_972.2, 22_574.64, 0),
        (3_801.2, 8_955.84, 0),
        (9_412, 12_000, 1_482.4),
        (14_071.2, 17_170, 1_380.24),
        (9_412, 9_592.34, 1_963.93),
        (3_801.2, 14_832.24, 0),
        (5_972.2, 22_594.64, 0),
        (3_801.2, 8_955.84, 969.07),
        (9_412, 12_000, 1_482.4),
        (14_071.2, 17_150, 1_384.24),
        (9_412, 9_592.34, 1_963.93),
        (3_801.2, 14_812.24, 0),
        (5_972.2, 22_574.64, 0),
        (3_801.2, 8_955.84, 969.07),
        (3_801.2, 12_672.24, 225.79),
        (3_801.2, 12_672.24, 0),
        (3_801.2, 12_672.24, 0),
        (3_801.2, 12_672.24, 0),
        (3_801.2, 12_672.24, 2_000),
    ],
    2024: [
        (12_230.4, 12_000, 2_000),
        (18_304, 17_166, 2_000),
        (12_230.4, 0, 2_000),
        (4_706, 15_650.8, 0),
        (7_397, 23_984.2, 0),
        (4_706, 9_000, 0),
        (12_230.4, 12_000, 2_000),
        (18_304, 17_189.06, 2_000),
        (12_230.4, 0, 2_000),
        (4_706, 15_673.86, 0),
        (7_397, 24_007.26, 0),
        (4_706, 9_000, 1_141.2),
        (12_230.4, 12_000, 2_000),
        (18_304, 17_166, 2_000),
        (12_230.4, 0, 2_000),
        (4_706, 15_650.8, 0),
        (7_397, 23_984.2, 0),
        (4_706, 9_000, 1_141.2),
        (4_706, 13_331.2, 274.96),
        (4_706, 13_331.2, 0),
        (4_706, 13_331.2, 0),
        (4_706, 13_331.2, 0),
        (4_706, 13_331.2, 2_000),
    ],
    2026: [
        (13_312, 12_000, 2_000),
        (19_934.2, 17_166, 2_000),
        (12_376, 0, 2_000),
        (4_968.6, 15_726.2, 0),
        (7_807.8, 24_109, 0),
        (4_968.6, 9_000, 0),
        (13_312, 12_000, 2_000),
        (19_934.2, 17_205.67, 2_000),
        (13_312, 0, 2_000),
        (4_968.6, 15_750.5, 0),
        (7_807.8, 24_148.67, 0),
        (4_968.6, 9_000, 1_193.72),
        (13_312, 12_000, 2_000),
        (19_934.2, 17_166, 2_000),
        (13_312, 0, 2_000),
        (4_968.6, 15_726.2, 0),
        (7_807.8, 24_109, 0),
        (4_968.6, 9_000, 1_193.72),
        (4_968.6, 13_406.6, 312.4),
        (4_968.6, 13_406.6, 0),
        (4_968.6, 13_406.6, 0),
        (4_968.6, 13_406.6, 0),
        (4_968.6, 13_406.6, 2_000),
    ],
}


@pytest.mark.parametrize("year", sorted(ORIGIN_MAIN))
def test_matches_origin_main_on_unchanged_households(year):
    result = calculate(UNCHANGED_HOUSEHOLDS, year, DIFFERENTIAL_OUTPUTS)
    observed = np.stack([result[name] for name in DIFFERENTIAL_OUTPUTS], axis=1)
    np.testing.assert_allclose(observed, ORIGIN_MAIN[year], atol=0.01, rtol=0)
