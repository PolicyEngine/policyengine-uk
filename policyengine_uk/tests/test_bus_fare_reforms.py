"""Exercise data loading, nonlinear calendar dates and real Scenario reforms."""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.system import system
from policyengine_uk.utils.bus_fares import annual_capped_fare
from policyengine_uk.utils.scenario import Scenario


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def bus_dataset(region="SOUTH_EAST", journeys=True, zero=False):
    person = pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 1],
            "person_household_id": [1, 1],
            "age": [30, 30],
        }
    )
    if journeys:
        person["other_local_bus_trips"] = [0, 0] if zero else [100, 20]
        person["bus_in_london_trips"] = [0, 0]
        person["bus_pass_eligible"] = [False, False]
        person["local_bus_single_fare_share"] = [0.7, 0.7]
    return UKMultiYearDataset(
        datasets=[
            UKSingleYearDataset(
                person=person,
                benunit=pd.DataFrame({"benunit_id": [1]}),
                household=pd.DataFrame(
                    {
                        "household_id": [1],
                        "region": [region],
                        "bus_fare_spending": [999.0],
                    }
                ),
                fiscal_year=2024,
            )
        ]
    )


def projected_dataset(
    region="SOUTH_EAST", london_trips=(0, 0), other_trips=(100, 20), fares=None
):
    """A 2024 dataset that Simulation extends to later years, so journeys are
    supplied in each year. A UKMultiYearDataset supplies only its own years."""
    person = pd.DataFrame(
        {
            "person_id": [1, 2],
            "person_benunit_id": [1, 1],
            "person_household_id": [1, 1],
            "age": [30, 30],
            "bus_in_london_trips": list(london_trips),
            "other_local_bus_trips": list(other_trips),
            "bus_pass_eligible": [False, False],
            "local_bus_single_fare_share": [0.7, 0.7],
        }
    )
    if fares is not None:
        person["local_bus_uncapped_single_fare"] = list(fares)
    household = pd.DataFrame(
        {
            "household_id": [1],
            "region": [region],
            "tenure_type": ["OWNED_OUTRIGHT"],
            "council_tax": [1_500.0],
            "rent": [0.0],
            "household_weight": [1.0],
            "bus_fare_spending": [999.0],
        }
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=household,
        fiscal_year=2024,
    )


def test_england_fares_follow_each_area_index():
    # Trips set so 2024-25 spending is in the ratio of published receipts
    # (BUS05ai: London GBP 1,347.43m, England outside London GBP 2,069.95m).
    london = 1_347.434943 / (2.369144880275 * 1.017729905895)
    outside = 2_069.953713 / (1.12466920264 * 1.429858292587)
    simulation = Simulation(
        dataset=projected_dataset(london_trips=(london, 0), other_trips=(0, outside))
    )
    total = {
        year: simulation.calculate("bus_fare_spending", year)[0]
        for year in (2024, 2025)
    }
    assert total[2024] == pytest.approx(1_347.434943 + 2_069.953713, rel=1e-5)
    # Each area moves with its own BUS0415a index, FY2025-26 over FY2024-25:
    # London 196.1017 / 196.1 and England outside London 214.1797 / 190.2282.
    assert total[2025] == pytest.approx(
        1_347.434943 * 1.0000086 + 2_069.953713 * 1.1259092, rel=1e-5
    )
    # So England rises 7.6%, more than DfT's England index (205.616 / 193.297,
    # +6.4%). Its December 2024 to March 2025 step is 5.6%, against 11.0%
    # outside London and none in London, so it weights outside London at about
    # one half where receipts weight it at 61%.
    assert total[2025] / total[2024] == pytest.approx(1.0763, abs=1e-4)


# 100 trips by one passenger outside London: 112.47 boardings, 70% singles.
SINGLES = 100 * 1.12466920264 * 0.7


def spending_2025(**parameter_changes):
    simulation = Simulation(
        dataset=projected_dataset(other_trips=(100, 0)),
        scenario=Scenario(
            parameter_changes={
                path: {2025: value} for path, value in parameter_changes.items()
            }
        ),
    )
    return simulation.calculate("person_bus_fare_spending", 2025)[0]


def test_a_three_pound_cap_binds_and_cap_reforms_follow_the_table():
    cap = "gov.dft.bus.fares.cap"
    baseline = spending_2025()
    uncapped = spending_2025(**{cap: np.inf})
    two_pounds = spending_2025(**{cap: 2})
    assert uncapped > baseline > two_pounds
    # FY2025-26 fares are the FY2024-25 table times CPI (1.0337). Only the 13%
    # at GBP 3.95 is above GBP 3; a GBP 2 cap also takes the 31% at GBP 2.21
    # down to GBP 2.
    assert uncapped - baseline == pytest.approx(
        SINGLES * 0.13 * (3.95 * 1.0337 - 3), rel=1e-3
    )
    assert baseline - two_pounds == pytest.approx(
        SINGLES * (0.31 * (2.21 * 1.0337 - 2) + 0.13 * 1), rel=1e-3
    )


def test_scheduled_caps_enter_the_projected_baseline():
    simulation = Simulation(dataset=projected_dataset(other_trips=(100, 0)))
    bus = system.parameters.gov.dft.bus
    index = bus.local_bus_fares_index.ENGLAND_OUTSIDE_LONDON
    table = bus.uncapped_single_fares.fare

    def index_path(year):
        # The fares index projected with CPI, which holds the GBP 3 cap.
        ratio = index(f"{year}-01-01") / index("2024-01-01")
        return 100 * 1.12466920264 * 1.429858292587 * ratio

    def fare(band, year):
        return table.children[band](f"{year}-01-01")

    def spending(year):
        return simulation.calculate("person_bus_fare_spending", year)[0]

    # 2026-27: GBP 2 for the last 95 days, from 1 January 2027.
    middle = fare("MIDDLE", 2026)
    change = -(0.31 * (middle - 2) + 0.13 * (3 - 2)) * 95 / 365
    assert spending(2026) == pytest.approx(
        index_path(2026) + SINGLES * change, rel=1e-5
    )
    # 2027-28 runs to 5 April 2028, 366 days: GBP 2 for 270, then no cap
    # from 1 January 2028 for 96.
    middle, high = fare("MIDDLE", 2027), fare("HIGH", 2027)
    change = (
        -(0.31 * (middle - 2) + 0.13 * (3 - 2)) * 270 + 0.13 * (high - 3) * 96
    ) / 366
    assert spending(2027) == pytest.approx(
        index_path(2027) + SINGLES * change, rel=1e-5
    )
    # From 2028-29 there is no cap, so the 13% above GBP 3 pay in full.
    change = 0.13 * (fare("HIGH", 2028) - 3)
    assert spending(2028) == pytest.approx(
        index_path(2028) + SINGLES * change, rel=1e-5
    )


def test_a_supplied_uncapped_fare_replaces_the_table():
    simulation = Simulation(
        dataset=projected_dataset(other_trips=(100, 0), fares=(4, 4)),
        scenario=Scenario(parameter_changes={"gov.dft.bus.fares.cap": {2025: 2}}),
    )
    # The dataset's fare rises with CPI like other prices (2025: +3.37%).
    assert simulation.calculate("local_bus_uncapped_single_fare", 2025)[
        0
    ] == pytest.approx(4 * 1.0337)
    # Every single ticket costs GBP 4.13, so a GBP 2 cap in place of GBP 3
    # saves GBP 1 on each, against GBP 0.22 on average with the table.
    reformed = simulation.calculate("person_bus_fare_spending", 2025)[0]
    baseline = simulation.baseline.calculate("person_bus_fare_spending", 2025)[0]
    assert baseline == pytest.approx(spending_2025(), rel=1e-6)
    assert baseline - reformed == pytest.approx(SINGLES * 1, rel=1e-5)


def test_uncapped_fare_shares_must_sum_to_one():
    with pytest.raises(ValueError, match="sum to one"):
        spending_2025(**{"gov.dft.bus.uncapped_single_fares.share.HIGH": 0.5})


def test_loaded_total_does_not_mask_journeys_or_cap_reforms():
    simulation = Simulation(
        dataset=bus_dataset(),
        scenario=Scenario(parameter_changes={"gov.dft.bus.fares.cap": {2024: np.inf}}),
    )
    # Published 2024-25 receipts / priced boardings, translated from trips.
    k = 1_850_509_887.26131 / (28.0685543170643 * 58_620_101)
    priced_boardings = 1_850_509_887.26131 - 402_846_350.14539
    benchmark = 2_069_953_713.42079 / priced_boardings
    # In 2024-25 the cap was GBP 2 for 270 days and GBP 3 for 95. Without it,
    # the 31% of singles at GBP 2.21 and the 13% at GBP 3.95 pay in full.
    saving = 0.31 * 0.21 * 270 / 365 + 0.13 * (1.95 * 270 / 365 + 0.95 * 95 / 365)
    uncapped_yield = benchmark + 0.7 * saving
    baseline_people = np.array([100, 20]) * k * benchmark
    reformed_people = np.array([100, 20]) * k * uncapped_yield
    assert simulation.baseline.calculate(
        "person_bus_fare_spending", 2024
    ) == pytest.approx(baseline_people)
    assert simulation.calculate("person_bus_fare_spending", 2024) == pytest.approx(
        reformed_people
    )
    assert simulation.calculate("bus_fare_spending", 2024)[0] == pytest.approx(
        reformed_people.sum()
    )
    assert simulation.baseline.calculate("bus_fare_spending", 2024)[0] == pytest.approx(
        baseline_people.sum()
    )
    assert simulation.calculate("bus_fare_spending_reported", 2024)[0] == 999


def test_explicit_zero_journeys_replace_a_stale_positive_total():
    simulation = Simulation(dataset=bus_dataset(zero=True))
    assert simulation.calculate("bus_fare_spending", 2024)[0] == 0


@pytest.mark.parametrize("region", ["SOUTH_EAST", "WALES", "UNKNOWN"])
def test_legacy_fallback_and_proportional_reform(region):
    simulation = Simulation(
        dataset=bus_dataset(region, journeys=False),
        scenario=Scenario(parameter_changes={"gov.dft.bus.fare_index": {2024: 0.5}}),
    )
    # Calculating a default trip count must not make it a supplied zero.
    assert simulation.calculate("local_bus_trips", 2024).sum() == 0
    assert simulation.baseline.calculate("bus_fare_spending", 2024)[0] == 999
    assert simulation.calculate("bus_fare_spending", 2024)[0] == 499.5
    assert simulation.calculate("person_bus_fare_spending", 2024) == pytest.approx(
        [249.75, 249.75]
    )


def test_wales_keeps_reported_spending_even_with_journeys():
    simulation = Simulation(dataset=bus_dataset("WALES"))
    assert simulation.calculate("bus_fare_spending", 2024)[0] == 999


@pytest.mark.parametrize("region", ["SCOTLAND", "NORTHERN_IRELAND"])
def test_national_cap_reform_does_not_change_devolved_fares(region):
    simulation = Simulation(
        dataset=bus_dataset(region),
        scenario=Scenario(parameter_changes={"gov.dft.bus.fares.cap": {2024: 0}}),
    )
    assert simulation.calculate("bus_fare_spending", 2024)[0] > 0
    assert simulation.calculate("bus_fare_spending", 2024) == pytest.approx(
        simulation.baseline.calculate("bus_fare_spending", 2024)
    )


def test_ridership_multiplier_is_explicit_and_does_not_change_input_journeys():
    simulation = Simulation(
        dataset=bus_dataset(),
        scenario=Scenario(
            parameter_changes={"gov.dft.bus.ridership_index": {2024: 1.2}}
        ),
    )
    assert simulation.calculate("bus_fare_spending", 2024)[0] == pytest.approx(
        simulation.baseline.calculate("bus_fare_spending", 2024)[0] * 1.2
    )
    assert simulation.calculate("local_bus_trips", 2024).tolist() == [100, 20]


def test_caps_apply_before_annual_averaging_and_preserve_january_changes():
    schedule = system.parameters.gov.dft.bus.fares
    assert schedule("2024-12-31").cap == 2
    assert schedule("2025-01-01").cap == 3
    assert schedule("2026-12-31").cap == 3
    assert schedule("2027-01-01").cap == 2
    assert np.isinf(schedule("2028-01-01").cap)
    # A £2.50 fare is capped at £2 for 270 days, then costs £2.50 for 95.
    assert annual_capped_fare(2.5, schedule, 2024) == pytest.approx(
        (270 * 2 + 95 * 2.5) / 365
    )
    # The £2 cap returns part-way through the 2026 fiscal year.
    assert annual_capped_fare(4, schedule, 2026) == pytest.approx(
        (270 * 3 + 95 * 2) / 365
    )


def test_a_cap_change_part_way_through_a_year_keeps_its_date():
    simulation = Simulation(
        dataset=bus_dataset(),
        scenario=Scenario(
            parameter_changes={"gov.dft.bus.fares.cap": {"2026-10-01.2100-12-31": 1}}
        ),
    )
    bus = simulation.tax_benefit_system.parameters.gov.dft.bus
    assert bus.fares.cap.metadata["preserve_calendar_dates"]
    assert bus.reference_fares.cap.metadata["preserve_calendar_dates"]
    assert bus.fares("2026-09-30").cap == 3
    assert bus.fares("2026-10-01").cap == 1
    # 178 days at £3 from 6 April, then 187 at £1. Annualised, the change
    # would have waited for the 2027 calendar year.
    assert annual_capped_fare(4, bus.fares, 2026) == pytest.approx(
        (178 * 3 + 187 * 1) / 365
    )


def test_clone_does_not_lose_journey_input_provenance():
    original = Simulation(dataset=bus_dataset())
    expected = original.calculate("bus_fare_spending", 2024)[0]
    clone = original.clone()
    clone.delete_arrays("bus_fare_spending")
    clone.delete_arrays("person_bus_fare_spending")
    assert clone.calculate("bus_fare_spending", 2024)[0] == expected
    clone.delete_arrays("other_local_bus_trips")
    assert original.calculate("other_local_bus_trips", 2024).tolist() == [100, 20]
