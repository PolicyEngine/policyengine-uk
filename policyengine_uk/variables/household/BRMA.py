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
        # An input keeps applying in later years, as policyengine-core's
        # auto_carry_over_input_variables does for input-only variables,
        # unless the household has changed region since. Only regions already
        # known are compared: calculating region for an earlier year here
        # could cache the wrong value, because core returns region's default
        # for a year once a later year is known.
        earlier_periods = [
            known_period
            for known_period in household.get_holder("brma").get_known_periods()
            if known_period.start < period.start
        ]
        moved = np.zeros(household.count, dtype=bool)
        if earlier_periods:
            latest = max(earlier_periods, key=lambda known_period: known_period.start)
            # The region in effect in the latest year is the last one known at
            # or before it, or region's default if none is (core gives the
            # default then, without storing it). Every region known after it,
            # up to this year, must match it.
            region_holder = household.get_holder("region")
            branch_name = household.simulation.branch_name
            region_periods = [
                known_period
                for known_period in region_holder.get_known_periods()
                if known_period.start <= period.start
            ]
            up_to_latest = [
                known_period
                for known_period in region_periods
                if known_period.start <= latest.start
            ]
            if up_to_latest:
                start_region = region_holder.get_array(
                    max(up_to_latest, key=lambda known_period: known_period.start),
                    branch_name,
                )
            else:
                start_region = region_holder.default_array()
            later_regions = [
                region_holder.get_array(known_period, branch_name)
                for known_period in region_periods
                if known_period.start > latest.start
            ]
            known_regions = [
                np.asarray(known_region)
                for known_region in [start_region, *later_regions]
                if known_region is not None
            ]
            for known_region in known_regions[1:]:
                moved |= known_region != known_regions[0]
            if not moved.any():
                return household("brma", latest)
        region = household("region", period)
        region_default = select(
            [region == region_value for region_value in REGION_DEFAULT_BRMA],
            list(REGION_DEFAULT_BRMA.values()),
            default=BRMAName.MAIDSTONE,
        )
        if not earlier_periods:
            return region_default
        return where(moved, region_default, household("brma", latest).decode())
