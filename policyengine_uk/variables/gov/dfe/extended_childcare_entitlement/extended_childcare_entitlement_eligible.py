from policyengine_uk.model_api import *


class extended_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligibility for extended childcare entitlement"
    definition_period = YEAR
    defined_for = "would_claim_extended_childcare"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/13",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/14",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/15",
    )

    def formula(benunit, period, parameters):
        person = benunit.members

        # A qualifying child of working parents is a young child of the
        # description in reg 13, under compulsory school age and in England
        # (Childcare Act 2016 s.1(2)(a)-(c)).
        has_qualifying_child = benunit.any(
            person("extended_childcare_entitlement_qualifying_child", period)
        )

        # The parent and the parent's partner, if any, must meet the
        # conditions in regs 14 and 15 (Childcare Act 2016 s.1(2)(d)): the
        # claimant and partner of the benefit unit, not their children.
        claimant_or_partner = person("is_claimant_or_partner", period)
        meets_parent_and_partner_conditions = benunit.any(
            claimant_or_partner
        ) & benunit.all(
            person("extended_childcare_entitlement_work_condition", period)
            | ~claimant_or_partner
        )

        return has_qualifying_child & meets_parent_and_partner_conditions
