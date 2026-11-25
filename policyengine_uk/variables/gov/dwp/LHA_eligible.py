from policyengine_uk.model_api import *


class LHA_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligibility for Local Housing Allowance"
    documentation = (
        "Selects the Housing Benefit eligible-rent calculation. When true, "
        "housing_benefit_entitlement uses LHA_cap. Otherwise it uses "
        "max(0, benunit_rent - housing_benefit_meals_deduction). By default "
        "the flag holds where the benefit unit rents, no member lives in "
        "social housing, and the household's recorded accommodation type "
        "isn't a houseboat, caravan or mobile home; an unknown type leaves "
        "the flag to the renting and social housing checks. A supplied "
        "value selects the model's eligible-rent calculation independently "
        "of housing_benefit_eligible."
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
        # a rent allowance outside the LHA, a council in Great Britain
        # normally uses a rent officer's determination (regs 14 and 13), and
        # in Northern Ireland the Housing Executive decides (NI regs 15 and
        # 14). The eligible rent starts from the resulting maximum rent,
        # subject to adjustments (reg 12C; NI reg 13B). The model has no rent
        # officer's rent amount. Outside the LHA, housing_benefit_entitlement
        # uses max(0, benunit_rent - housing_benefit_meals_deduction), which
        # can exceed the eligible rent in law. The household's recorded
        # accommodation type stands in for the dwelling each of its benefit
        # units pays for.
        accommodation = benunit.value_from_first_person(
            benunit.members.household("accommodation_type", period)
        )
        mobile_home = accommodation == accommodation.possible_values.MOBILE
        return renting & ~anyone_in_social_housing & ~mobile_home
