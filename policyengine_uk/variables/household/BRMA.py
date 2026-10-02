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
        "an earlier year applies when the household's region is the same as "
        "in that year; otherwise the household is placed in its region's BRMA "
        "with the most private-rented households (Maidstone if the region is "
        "unknown)."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        region = household("region", period)
        region_default = select(
            [region == region_value for region_value in REGION_DEFAULT_BRMA],
            list(REGION_DEFAULT_BRMA.values()),
            default=BRMAName.MAIDSTONE,
        )
        # An input keeps applying in later years, as policyengine-core's
        # auto_carry_over_input_variables does for input-only variables. A
        # household whose region differs from that year's gets its new
        # region's default instead.
        earlier_periods = [
            known_period
            for known_period in household.get_holder("brma").get_known_periods()
            if known_period.start < period.start
        ]
        if not earlier_periods:
            return region_default
        latest = max(earlier_periods, key=lambda known_period: known_period.start)
        same_region = household("region", latest) == region
        return where(same_region, household("brma", latest).decode(), region_default)
