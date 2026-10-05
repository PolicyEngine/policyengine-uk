from policyengine_uk.model_api import *
from policyengine_uk.utils.bus_fares import annual_capped_fare, has_bus_journeys
from policyengine_uk.utils.supplied_inputs import supplied_input


class person_bus_fare_spending(Variable):
    label = "personal bus and coach fare spending"
    documentation = (
        "Fare-paying bus journeys priced at the published yield, with changes "
        "in the single-fare cap applied only to single-ticket boardings in "
        "England outside London. Without usable journey data, allocates "
        "reported household spending by age. See docs/engineering/bus-fares.md."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

    def formula(person, period, parameters):
        p = parameters(period).gov.dft.bus
        if p.prior_law_fare_index <= 0:
            raise ValueError("The reference bus fare index must be positive")
        fare_multiplier = max_(p.fare_index, 0) / p.prior_law_fare_index
        weight = p.fare_allocation_weight_by_age.calc(person("age", period))
        household_weight = person.household("household_bus_fare_age_weight", period)
        share = weight / where(household_weight > 0, household_weight, 1)
        # The YAML runner can receive an explicit household total directly.
        # UK Simulation moves such totals to the reported input on loading.
        reported = supplied_input(person.household, "bus_fare_spending", period)
        if reported is None:
            reported = person.household("bus_fare_spending_reported", period)
        else:
            reported = person.household.project(reported)
        fallback = reported * share * fare_multiplier
        if period.start.year < 2024 or not has_bus_journeys(person, period):
            return fallback

        region = person.household("region", period)
        regions = region.possible_values
        in_scotland = region == regions.SCOTLAND
        in_ni = region == regions.NORTHERN_IRELAND
        unpriced = (region == regions.WALES) | (region == regions.UNKNOWN)
        in_england = ~(in_scotland | in_ni | unpriced)
        london_trips = person("bus_in_london_trips", period)
        other_trips = person("other_local_bus_trips", period)
        if all(
            supplied_input(person, name, period) is None
            for name in ("bus_in_london_trips", "other_local_bus_trips")
        ):
            total = person("local_bus_trips", period)
            london_trips = where(region == regions.LONDON, total, 0)
            other_trips = where(region == regions.LONDON, 0, total)
        other_boardings = select(
            [in_scotland, in_ni],
            [p.boardings_per_trip.SCOTLAND, p.boardings_per_trip.NORTHERN_IRELAND],
            default=p.boardings_per_trip.ENGLAND_OUTSIDE_LONDON,
        )
        other_yield = select(
            [in_scotland, in_ni],
            [p.yield_per_boarding.SCOTLAND, p.yield_per_boarding.NORTHERN_IRELAND],
            default=p.yield_per_boarding.ENGLAND_OUTSIDE_LONDON,
        )
        uncapped = max_(person("local_bus_uncapped_single_fare", period), 0)
        current_single = annual_capped_fare(
            uncapped, parameters.gov.dft.bus.fares, period.start.year
        )
        reference_single = annual_capped_fare(
            uncapped, parameters.gov.dft.bus.reference_fares, int(p.reference_year)
        )
        single_share = clip(person("local_bus_single_fare_share", period), 0, 1)
        other_yield = max_(
            other_yield
            + in_england * single_share * (current_single - reference_single),
            0,
        )
        spending = (
            max_(london_trips, 0)
            * p.boardings_per_trip.LONDON
            * p.yield_per_boarding.LONDON
            + max_(other_trips, 0) * other_boardings * other_yield
        )
        spending *= (
            ~person("bus_pass_eligible", period)
            * fare_multiplier
            * max_(p.ridership_index, 0)
        )
        return where(unpriced, fallback, spending)


class household_bus_fare_age_weight(Variable):
    label = "household bus fare age weight"
    documentation = (
        "Sum of members' bus fare allocation weights, used to distribute "
        "reported household spending when journey pricing is unavailable."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        weight = parameters(period).gov.dft.bus.fare_allocation_weight_by_age.calc(
            household.members("age", period)
        )
        return household.sum(weight)
