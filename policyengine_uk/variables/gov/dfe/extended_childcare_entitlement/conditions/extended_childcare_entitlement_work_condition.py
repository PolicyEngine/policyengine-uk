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
        "condition, and a lone parent cannot qualify that way. Before "
        "1 December 2022, SI 2016/1257 reg 9 deemed only qualifying paid "
        "work, so the £100,000 limit still applied to that person (reg 4(5) "
        "and (7)), and a working partner paid or entitled to a listed benefit "
        "did not count (reg 9(3))."
    )
    definition_period = YEAR
    defined_for = "is_claimant_or_partner"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/14",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/15",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/18",
        "https://www.legislation.gov.uk/uksi/2016/1257/regulation/4/made",
        "https://www.legislation.gov.uk/uksi/2016/1257/regulation/9/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.extended_childcare_entitlement
        claimant_or_partner = person("is_claimant_or_partner", period)

        # Reg 14(3)/15(3): in qualifying paid work (the minimum income
        # requirement in reg 18) and adjusted net income not above £100,000.
        meets_work_and_income_conditions = (
            claimant_or_partner
            & person("in_work", period)
            & person("extended_childcare_entitlement_meets_income_requirements", period)
        )

        # SI 2016/1257 reg 9(3), before 1 December 2022: a working partner paid
        # or entitled to a listed benefit does not count as in qualifying paid
        # work for the other's reg 9 route.
        exclusion_criteria = list(p.exemption.partner_exclusion_criteria)
        partner_excluded = (
            add(person, period, exclusion_criteria) > 0
            if exclusion_criteria
            else np.zeros_like(meets_work_and_income_conditions, dtype=bool)
        )
        counts_as_working_partner = meets_work_and_income_conditions & ~partner_excluded

        # Reg 14(4)/15(4): limited capability for work or a specified benefit,
        # with a partner who meets reg 14(3)/15(3).
        partner_meets_work_and_income_conditions = (
            person.benunit.sum(counts_as_working_partner) - counts_as_working_partner
        ) > 0
        # SI 2016/1257 reg 4(5) and (7), before 1 December 2022: the £100,000
        # limit still applies to the person using this route.
        within_income_limit = person("adjusted_net_income", period) <= p.income.limit
        meets_income_limit_if_applies = within_income_limit | (
            not p.exemption.income_limit_applies
        )
        exempt_through_partner = (
            claimant_or_partner
            & person(
                "extended_childcare_entitlement_limited_capability_or_specified_benefit",
                period,
            )
            & partner_meets_work_and_income_conditions
            & meets_income_limit_if_applies
        )

        return meets_work_and_income_conditions | exempt_through_partner
