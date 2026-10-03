from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.locations import BRMAName
from policyengine_uk.variables.household.demographic.geography import Region

# The BRMA a household is placed in when none is input: the BRMA with the
# most private-rented households in the region, from the 2021 (England, Wales,
# Northern Ireland) and 2022 (Scotland) censuses mapped to BRMAs
# (parameters/gov/dwp/LHA/brma_private_rented_households.csv.gz).
# Microsimulation datasets set brma for every household and do not use this
# table. test_brma_region_default.py checks it against the CSV.
REGION_DEFAULT_BRMA = {
    Region.NORTH_EAST: BRMAName.TYNESIDE,
    Region.NORTH_WEST: BRMAName.CENTRAL_GREATER_MANCHESTER,
    Region.YORKSHIRE: BRMAName.LEEDS,
    Region.EAST_MIDLANDS: BRMAName.LEICESTER,
    Region.WEST_MIDLANDS: BRMAName.BIRMINGHAM,
    Region.EAST_OF_ENGLAND: BRMAName.CENTRAL_NORFOLK_NORWICH,
    Region.LONDON: BRMAName.INNER_SOUTH_EAST_LONDON,
    Region.SOUTH_EAST: BRMAName.SOUTHAMPTON,
    Region.SOUTH_WEST: BRMAName.BRISTOL,
    Region.WALES: BRMAName.CARDIFF,
    Region.SCOTLAND: BRMAName.LOTHIAN,
    Region.NORTHERN_IRELAND: BRMAName.BELFAST,
}


class brma(Variable):
    value_type = Enum
    possible_values = BRMAName
    default_value = BRMAName.MAIDSTONE
    entity = Household
    label = "Broad Rental Market Area"
    documentation = (
        "The Broad Rental Market Area whose Local Housing Allowance rates "
        "apply to the household. If it is not provided, the latest BRMA from "
        "an earlier year applies unless the household has changed region "
        "since; otherwise the household is placed in its region's BRMA with "
        "the most private-rented households (Maidstone if the region is "
        "unknown)."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        # Everything here is read from values already stored, without
        # calculating region or an earlier year's BRMA. Calculating region
        # for a year can cache the wrong value for an earlier one (core's
        # carry-over gives region's default for a year once a later year is
        # known), and a BRMA stored only on another branch can't be read here.
        branch_name = household.simulation.branch_name
        region_holder = household.get_holder("region")
        brma_holder = household.get_holder("brma")

        def latest_readable(holder, condition):
            known_periods = sorted(
                (
                    known_period
                    for known_period in holder.get_known_periods()
                    if condition(known_period)
                ),
                key=lambda known_period: known_period.start,
                reverse=True,
            )
            for known_period in known_periods:
                values = holder.get_array(known_period, branch_name)
                if values is not None:
                    return known_period, values
            return None, None

        def region_in(year):
            # The last region known at or before the year, as region's own
            # inputs carry forward, or region's default if none is.
            _, values = latest_readable(
                region_holder, lambda known: known.start <= year.start
            )
            return region_holder.default_array() if values is None else values

        region = region_in(period)
        region_default = select(
            [region == region_value for region_value in REGION_DEFAULT_BRMA],
            list(REGION_DEFAULT_BRMA.values()),
            default=BRMAName.MAIDSTONE,
        )
        # An input keeps applying in later years, as policyengine-core's
        # auto_carry_over_input_variables does for input-only variables,
        # unless the household has changed region since.
        latest, latest_brma = latest_readable(
            brma_holder, lambda known: known.start < period.start
        )
        if latest is None:
            return region_default
        start_region = np.asarray(region_in(latest))
        moved = np.zeros(household.count, dtype=bool)
        for known_period in region_holder.get_known_periods():
            if latest.start < known_period.start <= period.start:
                values = region_holder.get_array(known_period, branch_name)
                if values is not None:
                    moved |= np.asarray(values) != start_region
        if not moved.any():
            return latest_brma
        return where(moved, region_default, latest_brma.decode())
