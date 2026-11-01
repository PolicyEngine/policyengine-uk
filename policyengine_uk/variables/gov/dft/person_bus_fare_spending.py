from policyengine_uk.model_api import *
from policyengine_uk.utils.bus_fares import has_bus_journeys, single_fare_cap_change
from policyengine_uk.utils.supplied_inputs import supplied_input


class person_bus_fare_spending(Variable):
    label = "personal bus and coach fare spending"
    documentation = (
        "Fare-paying bus journeys priced at the published yield, moved by each "
        "area's published fares index, with changes in the single-fare cap "
        "applied only to single-ticket boardings in England outside London. "
        "Without usable journey data, allocates reported household spending "
        "by age. See docs/engineering/bus-fares.md."
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
        # Each area's benchmark yield moves with its published fares index.
        # Northern Ireland has no index, so its yield moves with CPI.
        benchmark = parameters(f"{int(p.benchmark_year)}-01-01").gov
        index = p.local_bus_fares_index
        benchmark_index = benchmark.dft.bus.local_bus_fares_index
        cpi_growth = (
            parameters(period).gov.economic_assumptions.indices.obr.consumer_price_index
            / benchmark.economic_assumptions.indices.obr.consumer_price_index
        )
        london_yield = (
            p.yield_per_boarding.LONDON * index.LONDON / benchmark_index.LONDON
        )
        other_yield = select(
            [in_scotland, in_ni],
            [
                p.yield_per_boarding.SCOTLAND
                * index.SCOTLAND
                / benchmark_index.SCOTLAND,
                p.yield_per_boarding.NORTHERN_IRELAND * cpi_growth,
            ],
            default=p.yield_per_boarding.ENGLAND_OUTSIDE_LONDON
            * index.ENGLAND_OUTSIDE_LONDON
            / benchmark_index.ENGLAND_OUTSIDE_LONDON,
        )
        # The index already reflects the cap in reference_fares. Add the
        # effect of the cap differing from it in the same year: scheduled
        # changes after the last published quarter, and reforms. Single
        # tickets cost the person's supplied uncapped fare, or else follow
        # the table of uncapped single fares.
        supplied_fare = supplied_input(person, "local_bus_uncapped_single_fare", period)
        if supplied_fare is None:
            bands = p.uncapped_single_fares
            shares = [bands.share.LOW, bands.share.MIDDLE, bands.share.HIGH]
            if min(shares) < 0 or abs(sum(shares) - 1) > 1e-6:
                raise ValueError(
                    "The shares in gov.dft.bus.uncapped_single_fares.share must "
                    "be non-negative and sum to one"
                )
            fares = [bands.fare.LOW, bands.fare.MIDDLE, bands.fare.HIGH]
        else:
            shares, fares = [1], [supplied_fare]
        cap_change = single_fare_cap_change(
            [max_(fare, 0) for fare in fares],
            shares,
            parameters.gov.dft.bus.fares,
            parameters.gov.dft.bus.reference_fares,
            period.start.year,
        )
        single_share = clip(person("local_bus_single_fare_share", period), 0, 1)
        other_yield = max_(
            other_yield + in_england * single_share * cap_change,
            0,
        )
        spending = (
            max_(london_trips, 0) * p.boardings_per_trip.LONDON * london_yield
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
