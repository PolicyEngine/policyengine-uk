"""A pensioner's Council Tax Reduction child amounts and tariff income.

Under their pensioner schemes, councils add an amount for each child or young
person in the family and, in Wales, a family premium (SI 2012/2885 Sch 1 para
6(1)(b)-(c) and Sch 2 paras 2-3; WSI 2013/3029 Sch 1 para 1(1)(b)-(c) and Sch
2 paras 2-3; SSI 2012/319 reg 20(b) and Sch 1 para 3). For 2018-19 to 2024-25
the Secretary of State limited England's child amounts to two unless a Child
Tax Credit award included more (SI 2017/1305 reg 7; SI 2025/39 reg 5(2)).
Councils treat a pensioner's capital as a weekly income of £1 for each £500,
or part of £500, over £10,000 (SI 2012/2885 Sch 1 para 37; WSI 2013/3029 Sch
1 para 31; SSI 2012/319 reg 27(2)), except on the Pension Credit routes. The
Secretary of State and Welsh Ministers count the excess up to £16,000; the
Scottish Ministers set no ceiling. council_tax_reduction_tariff_income
carries that pensioner tariff, and also the Welsh and Scottish working-age
tariffs, which these tests do not recompute.

Each invariant holds on a fixed route and status. The generated families
claim no Universal Credit, so neither capital nor a child can move a family
between the pensioner and working-age schemes, and the first invariant's
pensioners claim no Pension Credit, so capital cannot move them onto a
Pension Credit route. Off those routes both can move. For a
savings-credit-only pensioner, councils use the Secretary of State's
assessment, which includes Pension Credit's deemed income from capital, so
capital can raise their applicable income. A mixed-age couple who gain a
child, and so start to receive Universal Credit, move to the working-age
scheme, whose applicable amount can be lower.

1. For a pensioner off Pension Credit, tariff income is 52 times £1 for each
   £500, or part of £500, of capital above £10,000 (up to £16,000 in England
   and Wales), and it never falls as capital rises. Capital changes nothing
   else in the applicable income, and the award never rises with capital.
   Councils give no award where capital exceeds £16,000 (SI 2012/2885 reg
   11(2); WSI 2013/3029 reg 30; SSI 2012/319 reg 40), so Scotland's uncapped
   tariff changes no award.
2. For a family that claims no Universal Credit, adding a dependent child
   never lowers the applicable amount. For a pensioner, councils add 52 times
   the scheme's weekly rate for each extra child they count. In England from
   2018-19 to 2024-25, they count up to two children, or more where a Child
   Tax Credit award includes individual elements for more. In Wales, councils
   also add the family premium with the first child. The generated families
   report no Child Tax Credit, so none has an award.
3. A pensioner with no child and capital up to £10,000 gets no child amount,
   family premium or tariff income, and a working-age family gets no child
   amount or family premium, so their applicable amount and applicable income
   match main. Their awards match main too, except that Scottish and Welsh
   working-age families take theirs from the working-age route
   (council_tax_reduction_devolved_working_age). An English working-age family
   also gets no tariff income here, because its local scheme sets its own.
   test_matches_origin_main_on_unchanged_households checks that against values
   computed on main and, for those awards, by hand.
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
    "council_tax_reduction_tariff_income",
    "council_tax_benefit",
)
SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def situation(households, year):
    """Build one benefit unit and household for each specification in one
    simulation."""
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


def tariff(capital, country):
    # The Secretary of State and the Welsh Ministers count the excess "not
    # exceeding £16,000"; the Scottish Ministers set no ceiling in reg 27(2).
    counted = capital if country == "SCOTLAND" else min(capital, 16_000)
    return 52 * math.ceil(max(0, counted - 10_000) / 500)


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
    tariffs = result["council_tax_reduction_tariff_income"]
    np.testing.assert_allclose(
        tariffs, [tariff(c, base["country"]) for c in capitals], atol=0.01
    )
    assert (np.diff(tariffs) >= 0).all()
    # As capital rises, the model changes only the tariff income within the
    # applicable income.
    other_income = result["council_tax_reduction_applicable_income"] - tariffs
    np.testing.assert_allclose(other_income, other_income[0], atol=0.01)
    assert (np.diff(result["council_tax_benefit"]) <= 0.01).all()
    # Councils give no award where capital exceeds £16,000, so Scotland's
    # uncapped tariff changes no award.
    over_limit = np.asarray(capitals) > 16_000
    assert (result["council_tax_benefit"][over_limit] <= 0.01).all()


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
        tariff_income = result["council_tax_reduction_tariff_income"][index]
        if not pensioner[index]:
            assert child_amounts == premium == 0
            if spec["country"] == "ENGLAND":
                assert tariff_income == 0
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
    assert result["council_tax_reduction_tariff_income"][0] == 0


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
# We computed these on main at 9dd44e142 for UNCHANGED_HOUSEHOLDS, in order:
# applicable amount, applicable income and council_tax_benefit. In Scotland
# and Wales the working-age families with savings of 12,000, 16,000 and 8,000
# have working-age tariff income of 1 a week for each 250, or part, over
# 6,000: 24 * 52 = 1,248, 40 * 52 = 2,080 and 8 * 52 = 416 a year. Their awards
# come from the working-age route, which sets its own amount and income: 2,000
# less 20% of the excess of net earnings after the earnings disregard, plus that
# tariff income, over the personal allowance and child amounts. For example, the
# Welsh family with savings of 8,000 in 2026 has 9,000 - 5 * 52 + 416 = 9,156
# against 101.85 * 52 = 5,296.20, so an award of 1,228.04.
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
        (3_801.2, 16_080.24, 889.22),
        (5_972.2, 24_674.64, 460.78),
        (3_801.2, 9_371.84, 937.87),
        (9_412, 12_000, 1_482.4),
        (14_071.2, 17_150, 1_384.24),
        (9_412, 9_592.34, 1_963.93),
        (3_801.2, 16_060.24, 950.63),
        (5_972.2, 24_654.64, 376.27),
        (3_801.2, 9_371.84, 987.79),
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
        (4_706, 16_921.86, 1_165.19),
        (7_397, 26_087.26, 972.71),
        (4_706, 9_416, 1_110),
        (12_230.4, 12_000, 2_000),
        (18_304, 17_166, 2_000),
        (12_230.4, 0, 2_000),
        (4_706, 16_898.8, 1_214.42),
        (7_397, 26_064.2, 839.31),
        (4_706, 9_416, 1_171.88),
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
        (4_968.6, 16_998.5, 1_277.78),
        (7_807.8, 26_228.67, 1_172.19),
        (4_968.6, 9_416, 1_162.52),
        (13_312, 12_000, 2_000),
        (19_934.2, 17_166, 2_000),
        (13_312, 0, 2_000),
        (4_968.6, 16_974.2, 1_329.96),
        (7_807.8, 26_189, 1_034.31),
        (4_968.6, 9_416, 1_228.04),
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
