from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_category import LHACategory


class housing_benefit_LHA_category(Variable):
    value_type = Enum
    entity = BenUnit
    label = "LHA category of dwelling (Housing Benefit)"
    documentation = (
        "The Housing Benefit category of dwelling (HB Regs 2006 reg. "
        "13D(2)). The shared accommodation rate applies to a young individual "
        "with no non-dependant to whom the severe disability premium does not "
        "apply, and, as for Universal Credit, in shared accommodation. "
        "Otherwise the category follows the number of bedrooms in the size "
        "criteria, up to four. Housing Benefit has no claim by a member of a "
        "couple as a single person, so a couple is never a young individual. "
        "Universal Credit has its own category: see LHA_category."
    )
    definition_period = YEAR
    possible_values = LHACategory
    default_value = LHACategory.C
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/1997/1984/schedule/3B",
    )

    def formula(benunit, period, parameters):
        rooms = benunit("LHA_allowed_bedrooms", period.this_year)
        household = benunit.members.household
        is_shared = benunit.any(household("is_shared_accommodation", period.this_year))
        # HB Regs 2006 reg 13D(2)(a)(i): a young individual who has no
        # non-dependant residing with them and to whom Sch 3 para 14 (severe
        # disability premium) does not apply. A Universal Credit qualifying
        # young person who is not a Housing Benefit young person is a
        # non-dependant (reg. 3), which the household composition proxy does
        # not identify, so responsibility under either scheme also blocks it.
        young_individual = (
            benunit("is_housing_benefit_young_individual", period)
            & ~benunit("lha_renter_has_non_dependant", period)
            & ~benunit(
                "is_responsible_for_child_or_young_person_for_uc_or_housing_benefit",
                period,
            )
            & ~benunit("housing_benefit_severe_disability_premium_applies", period)
        )
        return select(
            [
                young_individual | is_shared,
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
