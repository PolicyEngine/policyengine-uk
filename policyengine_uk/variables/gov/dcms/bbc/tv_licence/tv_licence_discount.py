from policyengine_uk.model_api import *


class tv_licence_discount(Variable):
    label = "TV licence discount"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/365A",
        "https://www.gov.uk/government/news/bbc-and-governments-joint-statement-on-delaying-the-tv-licence-fee-for-over-75s",
        "https://www.gov.uk/free-discount-tv-licence",
    )

    def formula(household, period, parameters):
        person = household.members
        tv_licence = parameters(period).gov.dcms.bbc.tv_licence

        # Aged discount
        aged = person("age", period) >= tv_licence.discount.aged.min_age
        has_aged = household.any(aged)
        claims_pc = add(household, period, ["pension_credit"]) > 0
        pc_requirement_share = tv_licence.discount.aged.must_claim_pc
        aged_discount_share = where(claims_pc, 1, 1 - pc_requirement_share)
        aged_discount = (
            has_aged * aged_discount_share * tv_licence.discount.aged.discount
        )

        # Blind discount
        is_blind = person("is_blind", period)
        has_blind = household.any(is_blind)
        blind_discount = has_blind * tv_licence.discount.blind.discount

        return max_(aged_discount, blind_discount)
