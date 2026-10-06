from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


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
        claims_pc = add(household, period, ["pension_credit"]) > 0
        aged_discount = 0
        for aged_rules, share in fiscal_year_segments(
            parameters.gov.dcms.bbc.tv_licence.discount.aged,
            period.start.year,
        ):
            aged = person("age", period) >= aged_rules.min_age
            has_aged = household.any(aged)
            meets_pc_requirement = not_(aged_rules.must_claim_pc) | claims_pc
            aged_discount += (
                has_aged * meets_pc_requirement * aged_rules.discount * share
            )

        # Blind discount
        is_blind = person("is_blind", period)
        has_blind = household.any(is_blind)
        blind_discount = has_blind * tv_licence.discount.blind.discount

        return max_(aged_discount, blind_discount)
