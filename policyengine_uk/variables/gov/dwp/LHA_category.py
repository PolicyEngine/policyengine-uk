from policyengine_uk.model_api import *


class LHACategory(Enum):
    A = "Shared accommodation"
    B = "One bedroom"
    C = "Two bedrooms"
    D = "Three bedrooms"
    E = "Four or more bedrooms"


class LHA_category(Variable):
    value_type = Enum
    entity = BenUnit
    label = "LHA category for the benefit unit, taking into account LHA rules on the number of LHA-covered bedrooms"
    documentation = (
        "The Universal Credit category of accommodation, which depends only "
        "on what the renter is entitled to: the shared accommodation rate "
        "for a specified renter, otherwise the category for the number of "
        "bedrooms in the size criteria. Whether the accommodation the renter "
        "actually occupies is shared does not matter, so a single renter "
        "aged 35 or over in a room gets the one-bedroom rate. Housing Benefit "
        "has its own category: see housing_benefit_LHA_category."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/25",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/27",
        "https://www.legislation.gov.uk/uksi/2013/382/schedule/1/paragraph/1",
    )
    definition_period = YEAR
    possible_values = LHACategory
    default_value = LHACategory.C

    def formula(benunit, period, parameters):
        # UC Regs 2013 Sch 4 para 25(1) step 1 and para 25(2)(b): the
        # category to which the renter is entitled under paras 8-12 and
        # 26-29.
        num_rooms = benunit("LHA_allowed_bedrooms", period.this_year)
        can_only_claim_shared = benunit(
            "is_lha_shared_accommodation_rate_specified_renter", period
        )
        return select(
            [
                can_only_claim_shared,
                num_rooms == 1,
                num_rooms == 2,
                num_rooms == 3,
                num_rooms > 3,
            ],
            [
                LHACategory.A,
                LHACategory.B,
                LHACategory.C,
                LHACategory.D,
                LHACategory.E,
            ],
        )
