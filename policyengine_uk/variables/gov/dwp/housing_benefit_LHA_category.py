from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_category import LHACategory


class housing_benefit_LHA_category(Variable):
    value_type = Enum
    entity = BenUnit
    label = "LHA category of dwelling (Housing Benefit)"
    documentation = (
        "The Housing Benefit category of dwelling. The shared accommodation "
        "rate applies to a young individual with no non-dependant, and to a "
        "claimant entitled to one bedroom who lacks exclusive use of "
        "self-contained accommodation, unless the severe disability premium "
        "applies. Otherwise the category follows the number of bedrooms in "
        "the Housing Benefit size criteria, up to four."
    )
    definition_period = YEAR
    possible_values = LHACategory
    default_value = LHACategory.C
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
        "https://www.legislation.gov.uk/uksi/1997/1984/schedule/3B",
    )

    def formula(benunit, period, parameters):
        rooms = benunit("housing_benefit_LHA_allowed_bedrooms", period.this_year)
        # Schedule 3 paragraph 14 (severe disability premium) applies.
        severe_disability = benunit(
            "housing_benefit_severe_disability_premium_applies", period
        )
        # HB Regs 2006 reg 13D(2)(a)(i).
        young_individual = (
            benunit("is_housing_benefit_young_individual", period)
            & ~benunit("housing_benefit_has_non_dependant", period)
            & ~severe_disability
        )
        # Reg 13D(2)(a)(ii): entitled to one bedroom but neither condition in
        # 13D(2)(b) is met.
        one_bedroom_shared = (
            (rooms == 1)
            & benunit("housing_benefit_shares_accommodation", period)
            & ~severe_disability
        )
        return select(
            [
                young_individual | one_bedroom_shared,
                rooms == 1,
                rooms == 2,
                rooms == 3,
                rooms > 3,
            ],
            [
                LHACategory.A,
                LHACategory.B,
                LHACategory.C,
                LHACategory.D,
                LHACategory.E,
            ],
        )
