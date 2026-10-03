from policyengine_uk.model_api import *


class extended_childcare_entitlement_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "meets the parent or partner conditions for extended childcare entitlement"
    documentation = (
        "Whether this parent or partner meets SI 2022/1134 reg 14(3) or 15(3): "
        "qualifying paid work, with at least the minimum income, and adjusted "
        "net income of no more than £100,000. Or whether they meet reg 14(4) "
        "or 15(4) instead: limited capability for work or a specified "
        "benefit, with a partner who meets reg 14(3) or 15(3). Under reg "
        "14(4) or 15(4) a person needs neither the work nor the income "
        "condition, and a lone parent cannot qualify that way."
    )
    definition_period = YEAR
    defined_for = "is_claimant_or_partner"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/14",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/15",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/18",
    )

    def formula(person, period, parameters):
        claimant_or_partner = person("is_claimant_or_partner", period)

        # Reg 14(3)/15(3): in qualifying paid work (the minimum income
        # requirement in reg 18) and adjusted net income not above £100,000.
        meets_work_and_income_conditions = (
            claimant_or_partner
            & person("in_work", period)
            & person("extended_childcare_entitlement_meets_income_requirements", period)
        )

        # Reg 14(4)/15(4): limited capability for work or a specified benefit,
        # with a partner who meets reg 14(3)/15(3).
        partner_meets_work_and_income_conditions = (
            person.benunit.sum(meets_work_and_income_conditions)
            - meets_work_and_income_conditions
        ) > 0
        exempt_through_partner = (
            claimant_or_partner
            & person(
                "extended_childcare_entitlement_limited_capability_or_specified_benefit",
                period,
            )
            & partner_meets_work_and_income_conditions
        )

        return meets_work_and_income_conditions | exempt_through_partner
