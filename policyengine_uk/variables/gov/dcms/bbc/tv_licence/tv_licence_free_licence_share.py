from policyengine_uk.model_api import *


class tv_licence_free_licence_share(Variable):
    label = "Share of the year covered by a free TV licence"
    documentation = (
        "Share of the year for which the household qualifies for the complete "
        "age-based TV licence exemption. This excludes the blind discount."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/365A",
        "https://www.gov.uk/free-discount-tv-licence",
    )

    def formula(household, period, parameters):
        person = household.members
        aged_discount = parameters(period).gov.dcms.bbc.tv_licence.discount.aged
        has_aged = household.any(person("age", period) >= aged_discount.min_age)
        claims_pc = add(household, period, ["pension_credit"]) > 0
        meets_pc_requirement = not_(aged_discount.must_claim_pc) | claims_pc
        return has_aged * meets_pc_requirement * aged_discount.discount
