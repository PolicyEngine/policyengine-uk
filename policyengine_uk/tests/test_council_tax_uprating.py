import functools
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation, parameters
from policyengine_uk.data import UKSingleYearDataset, economic_assumptions
from policyengine_uk.data.economic_assumptions import (
    apply_uprating,
    extend_single_year_dataset,
    household_weight_growth_path,
    reset_growthfactor_uprating,
    uprate_council_tax,
)
from policyengine_uk.variables.household.demographic.geography import Region


REGIONS = [region.name for region in Region]
UPRATED_YEARS = list(range(2023, 2032))
COUNCIL_TAX_GROWTH = parameters.gov.economic_assumptions.yoy_growth.obr.council_tax
# Household weights grow by the series uprating_indices.yaml lists them under.
# It is read from the file here, not from the code under test.
_UPRATING_INDICES = yaml.safe_load(
    (Path(economic_assumptions.__file__).parent / "uprating_indices.yaml").read_text()
)
(WEIGHT_GROWTH_PATH,) = [
    path for path, names in _UPRATING_INDICES.items() if "household_weight" in names
]
WEIGHT_GROWTH = parameters.get_child(WEIGHT_GROWTH_PATH)

# OBR council tax receipts in £ billion: the 2024-25 outturn from the March
# 2026 EFO (detailed forecast tables, expenditure, Table 4.1), then the
# 2025-26 outturn and the forecast to 2031-32 from the October 2026 EFO
# (Table 5.1).
OBR_RECEIPTS_YEARS = range(2024, 2032)
OBR_RECEIPTS = {
    "england": [41.2225, 44.117, 46.806, 49.2566, 52.0217, 54.9103, 57.8847, 60.9565],
    "scotland": [2.9384, 3.0519, 3.1699, 3.2924, 3.4196, 3.5518, 3.6891, 3.8316],
    "wales": [2.2284, 2.4008, 2.5784, 2.7691, 2.9739, 3.1939, 3.4301, 3.6839],
}

# The liability behind each country's OBR line, net of council tax reduction,
# by the year the fiscal year starts in (2022 is 2022-23).
PUBLISHED_OUTTURNS = {
    # MHCLG, Council Tax levels set by local authorities in England 2025 to
    # 2026, Table 1: council tax requirement including adult social care and
    # parish precepts, £ million. OBR's 2024-25 outturn is £41.2225bn.
    "england": {
        2022: 36_313.215616,
        2023: 38_718.300063,
        2024: 41_222.393749,
        2025: 44_118.104184,
    },
    # Scottish Government, Council Tax Collection Statistics 2024-25, Figure
    # 1: net amount billed, after council tax reduction and excluding water
    # and sewerage charges, £ thousand.
    "scotland": {2022: 2_825_646, 2023: 3_005_845, 2024: 3_076_770},
    # Welsh Government, Council tax collection rates for April 2022 to March
    # 2023, April 2023 to March 2024 and April 2024 to March 2025, Table 2:
    # in-year total debits, net of the council tax reduction scheme,
    # £ thousand.
    "wales": {2022: 1_981_608, 2023: 2_122_104, 2024: 2_331_585},
}


@functools.cache
def _country_of_each_region():
    # The model's own region-to-country mapping (the `country` variable), so
    # the expected growth below comes from a second path to the one the
    # uprating code takes. Built on first use, not at import: a system built
    # and dropped while the tests are collected would be frozen by conftest.py.
    people = {f"person_{region}": {"age": 40} for region in REGIONS}
    households = {
        f"household_{region}": {"members": [f"person_{region}"], "region": region}
        for region in REGIONS
    }
    sim = Simulation(situation={"people": people, "households": households})
    countries = sim.calculate("country", 2025)
    return dict(zip(REGIONS, countries))


@pytest.fixture(scope="module", autouse=True)
def release_region_mapping():
    # Drop the cached mapping once this module's tests are done, instead of
    # keeping it for the rest of the test process.
    yield
    _country_of_each_region.cache_clear()


def _series(region):
    # Council tax exists in England, Scotland and Wales; OBR forecasts it for
    # each. Northern Ireland levies domestic rates instead, so it has none. An
    # unknown region takes England's.
    country = _country_of_each_region()[region]
    if country == "NORTHERN_IRELAND":
        return None
    return "england" if country == "UNKNOWN" else country.lower()


def _expected_factor(region, year):
    # A bill grows by its country's receipts growth net of the growth in
    # household weights, so the country's weighted total grows by its
    # receipts growth (#2067). Northern Ireland's bills stay flat.
    series = _series(region)
    if series is None:
        return 1.0
    return (1 + COUNCIL_TAX_GROWTH.get_child(series)(year)) / (1 + WEIGHT_GROWTH(year))


def _uprated_council_tax(regions, council_tax, year):
    household_ids = np.arange(1, len(regions) + 1)
    previous_year = SimpleNamespace(
        household=pd.DataFrame(
            {"household_id": household_ids, "council_tax": council_tax}
        ),
        person=pd.DataFrame(),
    )
    current_year = SimpleNamespace(
        time_period=str(year),
        household=pd.DataFrame(
            {
                "household_id": household_ids,
                "region": regions,
                "council_tax": [0.0] * len(council_tax),
            }
        ),
        person=pd.DataFrame(),
    )
    uprate_council_tax(current_year, previous_year, parameters)
    return current_year.household["council_tax"].to_numpy()


def test_uprate_council_tax_holds_northern_ireland_flat():
    # In 2025-26 OBR's council tax receipts grow 7.02% in England, 7.73% in
    # Wales and 3.86% in Scotland (October 2026 EFO, Table 5.1, over the March
    # 2026 EFO's 2024-25 outturn), and household weights grow 0.33%, with
    # population. So a £1,000 bill becomes
    # £1,000 x 1.0702 / 1.0033 = £1,066.68 in London,
    # £1,000 x 1.0773 / 1.0033 = £1,073.76 in Wales and
    # £1,000 x 1.0386 / 1.0033 = £1,035.18 in Scotland. Northern Ireland has
    # no council tax series and keeps £1,000; it used to fall through to
    # England's growth, because the code compared the region with
    # "NORTHERN IRELAND" (a space) while the dataset label is NORTHERN_IRELAND.
    council_tax = _uprated_council_tax(
        ["LONDON", "WALES", "SCOTLAND", "NORTHERN_IRELAND"], [1_000.0] * 4, 2025
    )

    assert council_tax == pytest.approx(
        [1_066.68, 1_073.76, 1_035.18, 1_000.0], abs=0.005
    )


def test_uprate_council_tax_gives_unknown_region_england_growth():
    council_tax = _uprated_council_tax(["UNKNOWN"], [1_000.0], 2025)

    assert council_tax == pytest.approx([1_066.68], abs=0.005)


def test_scottish_bills_grow_with_the_amount_billed_in_2024_25():
    # Scotland's average Band D rose 0.1% in 2024-25, from £1,416.50 to
    # £1,418.11 (Scottish Government, Band D Council Tax 1996-97 to 2026-27),
    # but the net amount billed rose 2.36%, from £3,005.8m to £3,076.8m, and
    # household weights grow 0.97%. So a £1,000 bill becomes
    # £1,000 x 1.0236 / 1.0097 = £1,013.77. Dividing the Band D growth the
    # series used to hold for 2024 (0.001) by the weights' growth would have
    # cut it to £991.38, and Scotland's total would have grown 0.1%, not 2.36%.
    council_tax = _uprated_council_tax(["SCOTLAND"], [1_000.0], 2024)

    assert council_tax == pytest.approx([1_013.77], abs=0.005)


@pytest.mark.parametrize("region", ["NORTHERN IRELAND", "ATLANTIS", ""])
def test_uprate_council_tax_rejects_unrecognised_regions(region):
    # An unrecognised label used to get England's growth silently, which is
    # how the Northern Ireland typo went unnoticed.
    with pytest.raises(ValueError, match="unrecognised regions"):
        _uprated_council_tax(["LONDON", region], [1_000.0, 1_000.0], 2025)


@pytest.mark.parametrize(
    "series, year",
    [
        (series, year)
        for series, years in PUBLISHED_OUTTURNS.items()
        for year in sorted(years)[1:]
    ],
)
def test_council_tax_growth_matches_published_outturns(series, year):
    """Each outturn year is the growth in the published liability, rounded to
    4 decimals. England's 2025 value is an OBR forecast, and matches MHCLG's
    2025-26 requirement too: both lines measure the same thing."""
    outturns = PUBLISHED_OUTTURNS[series]
    published = outturns[year] / outturns[year - 1] - 1

    assert COUNCIL_TAX_GROWTH.get_child(series)(year) == pytest.approx(
        round(published, 4), abs=1e-12
    )


def test_household_weight_growth_path_is_the_index_that_grows_weights():
    assert household_weight_growth_path() == WEIGHT_GROWTH_PATH


@pytest.mark.parametrize(
    "uprating",
    [
        {"a": ["rent"]},
        {"a": ["household_weight"], "b": ["household_weight", "rent"]},
    ],
)
def test_household_weight_growth_path_needs_exactly_one_index(uprating):
    with pytest.raises(ValueError, match="exactly one"):
        household_weight_growth_path(uprating)


@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    households=st.lists(
        st.tuples(
            st.sampled_from(REGIONS),
            st.floats(0, 50_000, allow_nan=False),
        ),
        min_size=1,
        max_size=30,
    ),
    year=st.sampled_from(UPRATED_YEARS),
    scale=st.floats(0, 10, allow_nan=False),
)
def test_uprate_council_tax_properties(households, year, scale):
    """For every region in the Region enum, any council tax of zero or more
    and every uprated year:

    - council tax grows by its country's OBR series net of the growth in
      household weights, with the country taken from the model's `country`
      variable: England's for English regions and unknown regions, Scotland's
      and Wales's for those countries;
    - a Northern Ireland household's council tax is unchanged;
    - each household's result depends only on its own row;
    - scaling every previous-year amount scales every result by the same
      factor.
    """
    regions, amounts = (list(column) for column in zip(*households))

    council_tax = _uprated_council_tax(regions, amounts, year)

    expected = [
        amount * _expected_factor(region, year) for region, amount in households
    ]
    assert council_tax == pytest.approx(expected)
    northern_ireland = np.array(regions) == "NORTHERN_IRELAND"
    assert (council_tax[northern_ireland] == np.array(amounts)[northern_ireland]).all()
    alone = [
        _uprated_council_tax([region], [amount], year)[0]
        for region, amount in households
    ]
    assert council_tax == pytest.approx(alone)
    scaled = _uprated_council_tax(regions, [scale * amount for amount in amounts], year)
    assert scaled == pytest.approx(scale * council_tax)


def _dataset(regions, council_tax, weights=1.0, fiscal_year=2023):
    ids = np.arange(1, len(regions) + 1)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": 40,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": weights,
                "region": regions,
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": council_tax,
            }
        ),
        fiscal_year=fiscal_year,
    )


def _weighted_totals(dataset):
    """Each council tax series' weighted council tax total."""
    household = dataset.household
    series = household["region"].astype(str).map(_series)
    weighted = household["household_weight"] * household["council_tax"]
    return weighted.groupby(series.fillna("none")).sum().to_dict()


def test_country_totals_track_obr_receipts():
    """Project a dataset from 2024-25 to 2031-32 with unequal weights and
    bills. Each country's weighted council tax total grows as OBR forecasts
    its receipts to grow. Each year's growth is within 0.0001 of OBR's: the
    series rounds each year to 4 decimals, and holds Wales at 0.0740 from
    2026, where Table 5.1 implies 0.0739 to 0.0740. Before #2067 the totals
    also grew with the weights, by population, and were 2.8% too high by
    2030-31.
    """
    regions = ["LONDON", "NORTH_EAST", "SOUTH_WEST", "SCOTLAND", "SCOTLAND", "WALES"]
    dataset = _dataset(
        regions,
        council_tax=[2_100.0, 1_500.0, 2_400.0, 1_400.0, 1_900.0, 2_000.0],
        weights=[3_000.0, 1_000.0, 2_500.0, 1_200.0, 800.0, 1_500.0],
        fiscal_year=2024,
    )
    projected = extend_single_year_dataset(dataset, parameters, end_year=2031)
    totals = {year: _weighted_totals(projected[year]) for year in OBR_RECEIPTS_YEARS}

    for series, receipts in OBR_RECEIPTS.items():
        receipts = dict(zip(OBR_RECEIPTS_YEARS, receipts))
        for year in OBR_RECEIPTS_YEARS[1:]:
            growth = totals[year][series] / totals[year - 1][series] - 1
            obr_growth = receipts[year] / receipts[year - 1] - 1
            assert growth == pytest.approx(obr_growth, abs=1e-4), (series, year)
        assert totals[2031][series] / totals[2024][series] == pytest.approx(
            receipts[2031] / receipts[2024], rel=5e-4
        ), series


@settings(max_examples=30, deadline=None, derandomize=True)
@given(
    households=st.lists(
        st.tuples(
            st.sampled_from(REGIONS),
            st.floats(0, 50_000, allow_nan=False),
            st.floats(0.01, 10_000, allow_nan=False),
        ),
        min_size=1,
        max_size=12,
    ),
    base_year=st.integers(2022, 2030),
    years=st.integers(1, 2),
)
def test_each_country_total_grows_by_its_receipts_growth(households, base_year, years):
    """For any households in any regions, with any council tax of zero or
    more and any positive weights, any base year from 2022 and every year it
    is projected to:

    - each country's weighted council tax total grows by that country's
      receipts growth, with unknown regions counted with England;
    - each bill grows by its country's receipts growth net of the growth in
      household weights;
    - Northern Ireland's bills stay flat, so its weighted total grows with
      the weights alone.
    """
    regions, amounts, weights = (list(column) for column in zip(*households))
    dataset = _dataset(regions, amounts, weights, fiscal_year=base_year)

    projected = extend_single_year_dataset(
        dataset, parameters, end_year=base_year + years
    )

    for year in range(base_year + 1, base_year + years + 1):
        previous, current = projected[year - 1], projected[year]
        before, after = _weighted_totals(previous), _weighted_totals(current)
        for series, total in after.items():
            growth = (
                WEIGHT_GROWTH(year)
                if series == "none"
                else COUNCIL_TAX_GROWTH.get_child(series)(year)
            )
            assert total == pytest.approx(
                before[series] * (1 + growth), rel=1e-9, abs=1e-6
            ), (series, year)
        assert current.household["council_tax"].to_numpy() == pytest.approx(
            previous.household["council_tax"].to_numpy()
            * [_expected_factor(region, year) for region in regions]
        )


# The tests below use one household in each of the twelve regions that have a
# country.
KNOWN_REGIONS = [region for region in REGIONS if region != "UNKNOWN"]


def _one_household_per_known_region(council_tax):
    return _dataset(KNOWN_REGIONS, council_tax)


def _compounded(amount, region, year, base_year=2023):
    return amount * np.prod(
        [_expected_factor(region, y) for y in range(base_year + 1, year + 1)]
    )


def test_extended_dataset_compounds_each_country_council_tax_growth():
    # Projecting a dataset forward chains the yearly uprating, so each year's
    # council tax is the base amount times the product of its country's
    # growth factors since the base year.
    extended = extend_single_year_dataset(
        _one_household_per_known_region(1_500.0), parameters, end_year=2030
    )

    for year in range(2024, 2031):
        council_tax = extended[year].household["council_tax"].to_numpy()
        assert council_tax == pytest.approx(
            [_compounded(1_500.0, region, year) for region in KNOWN_REGIONS]
        )
        assert council_tax[KNOWN_REGIONS.index("NORTHERN_IRELAND")] == 1_500.0


def test_microsimulation_holds_northern_ireland_council_tax_flat():
    sim = Microsimulation(dataset=_one_household_per_known_region(1_500.0))

    for year in (2026, 2030):
        council_tax = sim.calculate("council_tax", year).values
        assert council_tax == pytest.approx(
            [_compounded(1_500.0, region, year) for region in KNOWN_REGIONS]
        )
        council_tax = dict(zip(KNOWN_REGIONS, council_tax))
        assert council_tax["NORTHERN_IRELAND"] == 1_500.0
        assert council_tax["LONDON"] > 1_500.0


def _reported_reduction_dataset():
    """Synthetic reports with person order independent of household order.

    The nonzero NI report is only a mechanical no-growth control, not a
    classification of any real NI benefit as Council Tax Reduction.
    """
    household_ids = [81, 17, 63, 45, 92]
    person_ids = [601, 230, 815, 407, 122, 944, 508, 736]
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": person_ids,
                "person_benunit_id": person_ids,
                "person_household_id": [17, 81, 92, 17, 63, 45, 92, 63],
                "age": 40,
                "council_tax_benefit_reported": [
                    1_000.0,
                    350.0,
                    600.0,
                    0.0,
                    125.0,
                    900.0,
                    200.0,
                    0.0,
                ],
            },
            index=[52, 11, 97, 6, 84, 3, 32, 75],
        ),
        benunit=pd.DataFrame({"benunit_id": person_ids}),
        household=pd.DataFrame(
            {
                "household_id": household_ids,
                "household_weight": [3.0, 2.0, 1.0, 4.0, 5.0],
                "region": [
                    "SCOTLAND",
                    "LONDON",
                    "NORTHERN_IRELAND",
                    "UNKNOWN",
                    "WALES",
                ],
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": [1_400.0, 2_000.0, 0.0, 1_800.0, 2_400.0],
            },
            index=[40, 12, 60, 8, 23],
        ),
        fiscal_year=2024,
    )


def _bill_per_person(dataset):
    bills = dataset.household.set_index("household_id")["council_tax"]
    return dataset.person["person_household_id"].map(bills).to_numpy()


@pytest.mark.parametrize("year", [2025, 2030])
def test_reported_reduction_keeps_each_persons_share_of_their_household_bill(year):
    # Issue #2674: uprating a report by generic CPI, a population-weight
    # factor, or another household's bill would each change these shares.
    base = _reported_reduction_dataset()
    original_people = base.person.copy(deep=True)
    projected = extend_single_year_dataset(base, parameters, end_year=year)[year]
    base_bills = _bill_per_person(base)
    projected_bills = _bill_per_person(projected)
    reports = base.person["council_tax_benefit_reported"].to_numpy()
    projected_reports = projected.person["council_tax_benefit_reported"].to_numpy()
    great_britain = base_bills > 0

    np.testing.assert_allclose(
        projected_reports[great_britain] / projected_bills[great_britain],
        reports[great_britain] / base_bills[great_britain],
        rtol=1e-12,
    )
    assert (projected_bills[great_britain] > base_bills[great_britain]).all()
    np.testing.assert_array_equal(projected_reports[~great_britain], [125.0, 0.0])
    np.testing.assert_array_equal(projected_bills[~great_britain], [0.0, 0.0])
    np.testing.assert_array_equal(projected_reports[reports == 0], [0.0, 0.0])
    pd.testing.assert_frame_equal(base.person, original_people)
    pd.testing.assert_index_equal(projected.person.index, base.person.index)


def test_council_tax_projection_does_not_create_an_absent_reported_reduction():
    base = _reported_reduction_dataset()
    base.person = base.person.drop(columns="council_tax_benefit_reported")
    original_people = base.person.copy(deep=True)

    projected = extend_single_year_dataset(base, parameters, end_year=2027)

    for year in projected.years:
        assert "council_tax_benefit_reported" not in projected[year].person
        pd.testing.assert_frame_equal(projected[year].person, original_people)
    assert projected[2027].household["council_tax"].iloc[1] > 2_000.0


@pytest.mark.parametrize(
    "previous_has_report,current_has_report",
    [(False, False), (True, False), (False, True)],
)
def test_reported_reduction_projection_preserves_sparse_person_tables(
    previous_has_report, current_has_report
):
    previous = _reported_reduction_dataset()
    current = previous.copy()
    current.time_period = "2025"
    if not previous_has_report:
        previous.person = previous.person.drop(columns="council_tax_benefit_reported")
    if not current_has_report:
        current.person = current.person.drop(columns="council_tax_benefit_reported")
    expected_people = current.person.copy(deep=True)

    uprate_council_tax(current, previous, parameters)

    pd.testing.assert_frame_equal(current.person, expected_people)
    assert current.household["council_tax"].iloc[1] > 2_000.0


def test_reset_restores_reported_reduction_and_reprojection_is_deterministic():
    base = _reported_reduction_dataset()
    projected = extend_single_year_dataset(base, parameters, end_year=2027)
    frozen = reset_growthfactor_uprating(projected.copy())

    for year in frozen.years:
        np.testing.assert_array_equal(
            frozen[year].person["council_tax_benefit_reported"],
            base.person["council_tax_benefit_reported"],
        )
        np.testing.assert_array_equal(
            frozen[year].household["council_tax"], base.household["council_tax"]
        )

    reprojected = apply_uprating(frozen, parameters, copy=False)
    for year in projected.years:
        np.testing.assert_allclose(
            reprojected[year].person["council_tax_benefit_reported"],
            projected[year].person["council_tax_benefit_reported"],
            rtol=1e-12,
        )
        np.testing.assert_allclose(
            reprojected[year].household["council_tax"],
            projected[year].household["council_tax"],
            rtol=1e-12,
        )


def test_unsupported_working_age_claim_keeps_half_the_projected_council_tax_bill():
    # Maidstone has no simulated working-age scheme. The public synthetic
    # observation pays half its bill; council_tax_benefit must retain that
    # share via its reported fallback, not merely store an uprated input.
    dataset = _dataset(["SOUTH_EAST"], [2_000.0], fiscal_year=2024)
    dataset.person["council_tax_benefit_reported"] = 1_000.0
    dataset.household["local_authority"] = "MAIDSTONE"
    simulation = Microsimulation(dataset=dataset)

    for year in (2024, 2027, 2030):
        np.testing.assert_array_equal(
            simulation.calculate("council_tax_reduction_scheme_supported", year),
            [False],
        )
        np.testing.assert_array_equal(
            simulation.calculate("council_tax_reduction_claimant_benunit", year),
            [True],
        )
        bill = simulation.calculate("council_tax", year).values
        report = simulation.calculate("council_tax_benefit_reported", year).values
        benefit = simulation.calculate("council_tax_benefit", year).values
        np.testing.assert_allclose(report, bill / 2, rtol=1e-6)
        np.testing.assert_allclose(benefit, bill / 2, rtol=1e-6)
