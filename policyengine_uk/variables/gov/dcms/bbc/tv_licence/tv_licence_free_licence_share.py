from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


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
        "https://www.gov.uk/government/news/bbc-and-governments-joint-statement-on-delaying-the-tv-licence-fee-for-over-75s",
        "https://www.gov.uk/free-discount-tv-licence",
    )

    def formula(household, period, parameters):
        person = household.members
        claims_pc = add(household, period, ["pension_credit"]) > 0
        free_licence_share = 0
        for aged_rules, share in fiscal_year_segments(
            parameters.gov.dcms.bbc.tv_licence.discount.aged,
            period.start.year,
        ):
            has_aged = household.any(person("age", period) >= aged_rules.min_age)
            meets_pc_requirement = not_(aged_rules.must_claim_pc) | claims_pc
            free_licence_share += (
                has_aged * meets_pc_requirement * aged_rules.discount * share
            )
        return free_licence_share
