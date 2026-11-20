from policyengine_uk.model_api import *


class LHA_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligibility for Local Housing Allowance"
    documentation = (
        "Whether the local authority caps the benefit unit's Housing Benefit "
        "eligible rent at the Local Housing Allowance: true where the benefit "
        "unit rents, no member lives in social housing, and the household "
        "doesn't live in a houseboat, caravan or mobile home."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13C",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13C",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/14C",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/14C",
    )

    def formula(benunit, period, parameters):
        renting = benunit("benunit_is_renting", period)
        anyone_in_social_housing = benunit.any(
            benunit.members("in_social_housing", period)
        )
        # A local authority determines no maximum rent (LHA) where the claim
        # relates to rent for "a houseboat, caravan or mobile home which he
        # occupies as his home" (SI 2006/213 and SI 2006/214 reg 13C(5)(d)(i);
        # Northern Ireland: SR 2006/405 and SR 2006/406 reg 14C(5)(d)(i)). For
        # most of these claims it refers the rent to a rent officer and sets
        # a maximum rent from the rent officer's determination (GB regs 14,
        # 13 and 12C); in Northern Ireland the Housing Executive decides (NI
        # regs 13B and 14). For an excluded tenancy, such as a pitch on a
        # council's own caravan site, the eligible rent is the rent less
        # ineligible charges (GB reg 12B and Sch 2). The model has no rent
        # officer determination, so housing_benefit_entitlement takes the
        # rent, less any charge for meals, as the eligible rent.
        accommodation = benunit.value_from_first_person(
            benunit.members.household("accommodation_type", period)
        )
        mobile_home = accommodation == accommodation.possible_values.MOBILE
        return renting & ~anyone_in_social_housing & ~mobile_home
