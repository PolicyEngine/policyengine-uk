from policyengine_uk.model_api import *


class tv_licence_discount(Variable):
    label = "TV licence discount"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/21/section/365A",
        "https://www.legislation.gov.uk/uksi/2022/693/pdfs/uksi_20220693_en.pdf",
        "https://www.gov.uk/government/news/bbc-and-governments-joint-statement-on-delaying-the-tv-licence-fee-for-over-75s",
        "https://www.gov.uk/free-discount-tv-licence",
        "https://www.gov.uk/government/publications/pension-credit-technical-guidance/a-detailed-guide-to-pension-credit-for-advisers-and-others",
        "https://www.nidirect.gov.uk/articles/free-tv-licences",
        "https://www.legislation.gov.uk/uksi/2004/692/regulation/5",
    )

    def formula(household, period, parameters):
        person = household.members
        tv_licence = parameters(period).gov.dcms.bbc.tv_licence

        # Aged discount
        aged = person("age", period) >= tv_licence.discount.aged.min_age
        has_aged = household.any(aged)
        receives_pc = person.benunit("pension_credit", period) > 0
        has_aged_with_pc = household.any(aged & receives_pc)
        pc_requirement_share = tv_licence.discount.aged.must_claim_pc
        aged_discount_share = where(
            has_aged_with_pc,
            1,
            1 - pc_requirement_share,
        )
        aged_discount = (
            has_aged * aged_discount_share * tv_licence.discount.aged.discount
        )

        # Blind discount
        is_blind = person("is_blind", period)
        has_blind = household.any(is_blind)
        blind_discount = has_blind * tv_licence.discount.blind.discount

        return max_(aged_discount, blind_discount)
