from openfisca_uk.model_api import *


class tv_licence_discount(Variable):
    label = "TV licence discount"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/365A",
        "https://www.tvlicensing.co.uk/reducedfee",
    )

    def formula(household, period, parameters):
        person = household.members
        tv_licence = parameters(period).gov.dcms.bbc.tv_licence

        # Aged discount
        aged = person("age", period) >= tv_licence.discount.aged.min_age
        has_aged = household.any(aged)
        claims_pc = add(household, period, ["pension_credit"]) > 0
        meets_pc_requirement = (
            tv_licence.discount.aged.must_claim_pc & claims_pc
        )
        aged_discount = (
            meets_pc_requirement & has_aged
        ) * tv_licence.discount.aged.discount

        # Blind discount
        is_blind = person("is_blind", period)
        blind_discount = (
            household.any(is_blind) * tv_licence.discount.blind.discount
        )

        return max_(aged_discount, blind_discount)
