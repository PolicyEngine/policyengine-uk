"""LHA rates against the published determinations.

The model recomputes each determination from April 2020 from the published
30th percentile rents, the national maxima and the rules of Schedule 3B to the
Rent Officers (Housing Benefit Functions) Order 1997 (and Schedule 1 to the
Universal Credit Functions Order 2013). These tests check that the recomputed
rates equal every published rate, and that the rules keep the properties the
law gives them under any freeze, percentile or maximum reform.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.utils.lha import (
    CATEGORIES,
    FIRST_RULES_YEAR,
    HELD_TABLES,
    PUBLISHED_RATES_PATH,
    determination_year,
    lha_rates,
    published_rates,
    restatement,
    statutory_percentile,
)
from policyengine_uk.variables.household.demographic.locations import BRMAName

SYSTEM = CountryTaxBenefitSystem()
TABLE = pd.read_csv(PUBLISHED_RATES_PATH)
LAST_PUBLISHED_YEAR = int(TABLE.year.max())

NORTHERN_IRELAND = {
    "BELFAST",
    "LOUGH_NEAGH_LOWER",
    "LOUGH_NEAGH_UPPER",
    "NORTH_NI",
    "NORTH_WEST_NI",
    "SOUTH_EAST_NI",
    "SOUTH_NI",
    "SOUTH_WEST_NI",
}


def wide(measure: str) -> pd.DataFrame:
    return TABLE.pivot_table(
        index=["year", "brma"], columns="lha_category", values=measure
    )[list(CATEGORIES)]


def test_every_brma_has_rates_for_every_determination_since_2020():
    """No BRMA falls back to a missing rate in a year the rules cover.

    Two gaps are known. No NIHE table for April 2026 could be retrieved; SR
    2026/2 holds Northern Ireland's rates at the January 2024 determination,
    which the model applies. And Northern Ireland's monthly Universal Credit
    rates are published (on nidirect) only from April 2024; before then the
    model converts the weekly percentile.
    """
    every = {member.name for member in BRMAName}
    for year in range(FIRST_RULES_YEAR, LAST_PUBLISHED_YEAR + 1):
        rows = TABLE[(TABLE.year == year) & TABLE.rate.notna()]
        expected = every - NORTHERN_IRELAND if year == 2026 else every
        assert set(rows.brma) == expected, year
        assert rows.groupby("brma").size().eq(len(CATEGORIES)).all(), year
        uc = TABLE[(TABLE.year == year) & TABLE.uc_rate.notna()]
        expected = every if year >= 2024 else every - NORTHERN_IRELAND
        assert set(uc.brma) == expected, year
        assert uc.groupby("brma").size().eq(len(CATEGORIES)).all(), year


def test_published_rates_never_fall_with_dwelling_size():
    """Schedule 3B paragraph 3 makes each category at least the one before.

    The raw percentile rents need not be (shared rooms can let for more than
    one-bedroom flats), which is why the paragraph exists.
    """
    for measure in ("rate", "uc_rate"):
        rates = wide(measure).dropna()
        falls = rates[(np.diff(rates.to_numpy(), axis=1) < 0).any(axis=1)]
        assert falls.empty, f"{measure} falls with size:\n{falls}"


WALES = {
    "BLAENAU_GWENT",
    "BRECON_AND_RADNOR",
    "BRIDGEND",
    "CAERPHILLY",
    "CARDIFF",
    "CARMARTHENSHIRE",
    "CEREDIGION",
    "FLINTSHIRE",
    "MERTHYR_CYNON",
    "MONMOUTHSHIRE",
    "NEATH_PORT_TALBOT",
    "NEWPORT",
    "NORTH_CLWYD",
    "NORTH_POWYS",
    "NORTH_WEST_WALES",
    "PEMBROKESHIRE",
    "SOUTH_GWYNEDD",
    "SWANSEA",
    "TAFF_RHONDDA",
    "TORFAEN",
    "VALE_OF_GLAMORGAN",
    "WREXHAM",
}


@pytest.mark.parametrize("frozen_year,determined_year", sorted(HELD_TABLES.items()))
@pytest.mark.parametrize("measure", ["rate", "uc_rate"])
def test_published_frozen_years_repeat_the_last_determination(
    frozen_year, determined_year, measure
):
    """SI 2020/1519, 2021/1380, 2023/6, 2025/5 and 2026/5 hold every rate.

    One known exception: Rent Officers Wales's tables for April 2022 and
    April 2023 (and DWP's monthly tables for Wales in those years) restate some
    of the April 2020 rates they say they hold. The model takes them as
    published (``restatement``); this pins the exception so that any other
    publisher repeating a held rate differently fails here.
    """
    rates = wide(measure)
    held = rates.loc[frozen_year].dropna()
    determined = rates.loc[determined_year].loc[held.index]
    differs = (held - determined).abs() > 0.004
    restated = set(held.index[differs.any(axis=1)])
    if (frozen_year, determined_year) in ((2022, 2020), (2023, 2020)):
        assert restated and restated <= WALES
        # The two restating tables agree with each other.
        if frozen_year == 2023:
            pd.testing.assert_frame_equal(held, rates.loc[2022].loc[held.index])
    else:
        assert not restated, sorted(restated)


@pytest.mark.parametrize("year", range(int(TABLE.year.min()), LAST_PUBLISHED_YEAR + 1))
@pytest.mark.parametrize("universal_credit", [False, True])
def test_model_reproduces_every_published_rate(year, universal_credit):
    """A differential test: the rules against the published tables."""
    measure = "uc_rate" if universal_credit else "rate"
    model = lha_rates(SYSTEM.parameters, year, universal_credit)
    published = published_rates().at(measure, year)
    have = ~np.isnan(published)
    assert not np.isnan(model["rate"][have]).any()
    mismatches = np.abs(model["rate"] - published) > 0.004
    rows, columns = np.nonzero(have & mismatches)
    assert len(rows) == 0, [
        (model["brmas"][i], CATEGORIES[j], model["rate"][i, j], published[i, j])
        for i, j in zip(rows[:10], columns[:10])
    ]


@pytest.mark.parametrize("year", range(2015, 2041))
def test_baseline_rates_are_defined_and_never_fall_with_size(year):
    for universal_credit in (False, True):
        rate = lha_rates(SYSTEM.parameters, year, universal_credit)["rate"]
        assert np.isfinite(rate).all() and (rate > 0).all(), year
        assert (np.diff(rate, axis=1) >= 0).all(), year


def test_years_map_to_april_determinations():
    """Parameters are read at 30 April, so a year is the fiscal year from April.

    The freeze for determinations in 2025 starts on 6 April 2025, so the 2025
    fiscal year is frozen at the January 2024 determination; the 2024 fiscal
    year carries the April 2024 reset.
    """
    lha = SYSTEM.parameters.gov.dwp.LHA
    assert determination_year(lha, 2024) == 2024
    assert determination_year(lha, 2025) == 2024
    assert determination_year(lha, 2026) == 2024
    assert determination_year(lha, 2023) == 2020
    assert determination_year(lha, 2020) == 2020


def test_statutory_percentile_positions():
    """Sch 3B para 2(8): mean of positions P and P+1 when 0.3N is whole."""
    ten = np.arange(1.0, 11.0)
    assert statutory_percentile(ten, 0.3) == pytest.approx(3.5)
    eleven = np.arange(1.0, 12.0)
    # 0.3 * 11 = 3.3, rounded up to position 4.
    assert statutory_percentile(eleven, 0.3) == pytest.approx(4.0)


# Property tests over reforms to the determination rules.


def reformed_parameters(
    freeze: dict, percentile: float, maximum_scale: float, minimum: bool
):
    """Copies of the LHA parameters with reforms applied by year."""
    lha = SYSTEM.parameters.gov.dwp.LHA.clone()
    for year, frozen in freeze.items():
        lha.freeze.update(period=str(year), value=frozen)
    for year in range(2020, 2041):
        lha.percentile.update(period=str(year), value=percentile)
        lha.march_2020_minimum.update(period=str(year), value=minimum)
        for node in (lha.maximum, lha.maximum_monthly):
            for category in CATEGORIES:
                parameter = node.children[category]
                parameter.update(
                    period=str(year),
                    value=round(parameter(str(year)) * maximum_scale, 2),
                )
    return SimpleNamespace(
        gov=SimpleNamespace(
            dwp=SimpleNamespace(LHA=lha),
            indices=SYSTEM.parameters.gov.indices,
        )
    )


reform_strategy = st.fixed_dictionaries(
    dict(
        freeze=st.dictionaries(st.integers(2020, 2032), st.booleans(), max_size=6),
        percentile=st.sampled_from([0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 0.9]),
        maximum_scale=st.sampled_from([0.25, 0.5, 1.0, 1.5]),
        minimum=st.booleans(),
    )
)


@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    reform=reform_strategy,
    year=st.integers(2020, 2032),
    universal_credit=st.booleans(),
)
def test_reformed_rates_keep_the_statutory_properties(reform, year, universal_credit):
    parameters = reformed_parameters(**reform)
    lha = parameters.gov.dwp.LHA
    measure = "uc_rate" if universal_credit else "rate"
    rate = lha_rates(parameters, year, universal_credit)["rate"]

    # Defined, positive, whole pence (para 2(10)) and never falling with
    # dwelling size (para 3), in every year, held or not.
    assert np.isfinite(rate).all() and (rate > 0).all()
    assert (np.diff(rate, axis=1) >= 0).all()
    assert np.allclose(rate * 100, np.round(rate * 100))

    determined = determination_year(lha, year)
    if determined != year:
        # A held year repeats the determination it is held at, wherever the
        # published tables do not restate the held rates.
        held = lha_rates(parameters, determined, universal_credit)["rate"]
        unrestated = (restatement(measure, determined, year) == 0).all(axis=1)
        np.testing.assert_array_equal(rate[unrestated], held[unrestated])
    if determined < FIRST_RULES_YEAR:
        # Held at a determination the model takes as published.
        return

    # The bounds the schedule puts on the determination itself.
    result = lha_rates(parameters, determined, universal_credit)
    rate, percentile = result["rate"], result["percentile"]
    maxima = lha.maximum_monthly if universal_credit else lha.maximum
    cap = np.array([maxima.children[c](str(determined)) for c in CATEGORIES])
    minimum = published_rates().at(measure, FIRST_RULES_YEAR) + restatement(
        measure, FIRST_RULES_YEAR, determined
    )
    floor = np.where(np.isnan(minimum), 0, minimum)
    applies = bool(lha.march_2020_minimum(str(determined)))
    # Never above the larger of the category maximum (raised by para 3 to any
    # smaller category's) and the minimum; never below the minimum while it
    # applies (para 3A); never below the lower of percentile and maximum.
    ceiling = np.maximum(np.maximum.accumulate(cap)[None, :], floor if applies else 0)
    assert (rate <= ceiling + 1e-9).all()
    if applies:
        assert (rate >= floor - 1e-9).all()
    assert (rate >= np.minimum(percentile, cap[None, :]) - 1e-9).all()


@settings(max_examples=25, deadline=None)
@given(
    year=st.integers(2020, 2032),
    low=st.sampled_from([0.1, 0.2, 0.3, 0.4]),
    step=st.sampled_from([0.05, 0.1, 0.3]),
    universal_credit=st.booleans(),
)
def test_a_higher_percentile_never_lowers_a_rate(year, low, step, universal_credit):
    unfrozen = {y: False for y in range(2020, 2033)}
    lower = lha_rates(
        reformed_parameters(unfrozen, low, 1.0, True), year, universal_credit
    )["rate"]
    higher = lha_rates(
        reformed_parameters(unfrozen, low + step, 1.0, True), year, universal_credit
    )["rate"]
    assert (higher >= lower - 1e-9).all()


# Reforms through a simulation.


def _weekly(year: int, brma: str, category: str, reform=None) -> float:
    situation = {
        "people": {"person": {"age": {year: 35}}},
        "benunits": {
            "benunit": {"members": ["person"], "LHA_category": {year: category}}
        },
        "households": {"household": {"members": ["person"], "brma": {year: brma}}},
    }
    annual = SYSTEM_SIMULATION(situation, reform).calculate("BRMA_LHA_rate", year)
    return float(annual[0]) / 52


def SYSTEM_SIMULATION(situation, reform):
    from policyengine_uk import Simulation

    return Simulation(situation=situation, reform=reform)


def test_unfreezing_a_published_year_uses_that_years_percentile():
    """The VOA publishes the percentile rents even for frozen years.

    Lifting the 2025 freeze therefore gives the rate that a 2025 determination
    would have produced: Maidstone two bedrooms, 30th percentile GBP 230.14
    (VOA, LHA April 2025, Table 2), against the held GBP 208.27.
    """
    assert _weekly(2025, "MAIDSTONE", "C") == pytest.approx(208.27, abs=0.001)
    unfrozen = _weekly(
        2025, "MAIDSTONE", "C", reform={"gov.dwp.LHA.freeze": {"2025": False}}
    )
    assert unfrozen == pytest.approx(230.14, abs=0.001)


def test_unfreezing_after_the_last_table_grows_the_latest_percentile():
    """Beyond the published tables, the latest percentile rent grows with rents."""
    index = SYSTEM.parameters.gov.indices.private_rent_index
    expected = (
        np.floor(np.round(253.15 * index("2027") / index("2026") * 100, 6) + 0.5) / 100
    )
    unfrozen = _weekly(
        2027,
        "MAIDSTONE",
        "C",
        reform={"gov.dwp.LHA.freeze": {"2027": False}},
    )
    assert unfrozen == pytest.approx(expected, abs=0.001)
    assert unfrozen > 253.15


def test_the_minimum_holds_rates_at_march_2020_levels():
    """Sch 3B para 3A: a lower percentile cannot take a rate below April 2020."""
    floor = 187.56  # Maidstone two bedrooms, LHA April 2020.
    low = _weekly(
        2024, "MAIDSTONE", "C", reform={"gov.dwp.LHA.percentile": {"2024": 0.01}}
    )
    assert low == pytest.approx(floor, abs=0.001)
    without_minimum = _weekly(
        2024,
        "MAIDSTONE",
        "C",
        reform={
            "gov.dwp.LHA.percentile": {"2024": 0.01},
            "gov.dwp.LHA.march_2020_minimum": {"2024": False},
        },
    )
    assert without_minimum < floor


def test_freezing_the_2024_reset_holds_the_2020_rates():
    held = _weekly(
        2024, "MAIDSTONE", "C", reform={"gov.dwp.LHA.freeze": {"2024": True}}
    )
    assert held == pytest.approx(187.56, abs=0.001)


def test_welsh_and_ni_percentile_ratios_use_the_english_median():
    """The Welsh and NI lists of rents in the file copy English ones.

    So a percentile reform scales their published rates by the median English
    ratio for the category, not by a copied list's shape.
    """
    from policyengine_uk.utils.lha import (
        NON_ENGLISH_REGIONS,
        _percentile_ratios,
        _sorted_list_of_rents,
        statutory_percentile,
    )

    lists, regions = _sorted_list_of_rents()
    ratios = _percentile_ratios(0.5)
    brmas = published_rates().brmas
    english = {category: [] for category in "ABCDE"}
    for (brma, category), rents in lists.items():
        if regions[brma] not in NON_ENGLISH_REGIONS:
            english[category].append(
                statutory_percentile(rents, 0.5) / statutory_percentile(rents, 0.3)
            )
    median = [np.median(english[category]) for category in "ABCDE"]
    for b in ("CARDIFF", "BELFAST"):
        np.testing.assert_allclose(ratios[brmas.get_loc(b)], median)
    assert (ratios >= 1).all()


def test_scottish_percentile_ratios_use_scotlands_own_lists():
    """Ratios from Rent Service Scotland's April 2020 lists (FOI 202200303624)."""
    from policyengine_uk.utils.lha import _percentile_ratios

    ratios = _percentile_ratios(0.5)
    brmas = published_rates().brmas
    assert ratios[brmas.get_loc("GREATER_GLASGOW"), 3] == pytest.approx(1.267, abs=5e-4)
    assert ratios[brmas.get_loc("LOTHIAN"), 2] == pytest.approx(1.091, abs=5e-4)


def test_scottish_lists_are_rent_service_scotlands_own():
    """Scotland's lists (FOI 202200303624) reproduce the published 30th
    percentiles and copy no English list, unlike the rows they replaced."""
    from policyengine_uk.utils.lha import (
        LIST_OF_RENTS_PATH,
        NON_ENGLISH_REGIONS,
        round_half_up,
        statutory_percentile,
    )

    rents = pd.read_csv(LIST_OF_RENTS_PATH)
    published = pd.read_csv(PUBLISHED_RATES_PATH).set_index(
        ["year", "brma", "lha_category"]
    )
    blocks = {
        key: tuple(np.sort(group.weekly_rent.to_numpy()))
        for key, group in rents.groupby(["region", "year", "brma", "lha_category"])
    }
    english = {
        rents
        for (region, *_), rents in blocks.items()
        if region not in NON_ENGLISH_REGIONS
    }
    scottish = {k: v for k, v in blocks.items() if k[0] == "SCOTLAND"}
    assert len(scottish) == 2 * 18 * 5
    assert not english & set(scottish.values())
    exact = sum(
        float(round_half_up(statutory_percentile(np.array(v), 0.3)))
        == pytest.approx(published.percentile_30[(year, brma, category)], abs=0.001)
        for (_, year, brma, category), v in scottish.items()
    )
    # 87 of 90 cells for April 2019 and 86 of 90 for April 2020 to the penny.
    assert exact >= 170
