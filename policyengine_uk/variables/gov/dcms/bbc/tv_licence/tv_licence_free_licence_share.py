from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class tv_licence_free_licence_share(Variable):
    label = "Share of the year covered by a free TV licence"
    documentation = (
        "Share of the year for which the household qualifies for the complete "
        "age-based TV licence exemption. Where Pension Credit is required, "
        "the qualifying older person must belong to the recipient's benefit "
        "unit. This excludes the blind discount."
    )
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
        receives_pc = person.benunit("pension_credit", period) > 0
        free_licence_share = 0
        for aged_rules, share in fiscal_year_segments(
            parameters.gov.dcms.bbc.tv_licence.discount.aged,
            period.start.year,
        ):
            aged = person("age", period) >= aged_rules.min_age
            has_aged = household.any(aged)
            has_aged_with_pc = household.any(aged & receives_pc)
            meets_pc_requirement = not_(aged_rules.must_claim_pc) | has_aged_with_pc
            free_licence_share += (
                has_aged * meets_pc_requirement * aged_rules.discount * share
            )
        return free_licence_share
