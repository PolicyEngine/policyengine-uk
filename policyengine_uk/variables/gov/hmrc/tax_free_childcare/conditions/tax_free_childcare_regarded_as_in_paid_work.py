from policyengine_uk.model_api import *


class tax_free_childcare_regarded_as_in_paid_work(Variable):
    value_type = bool
    entity = Person
    label = "regarded as in qualifying paid work for Tax-Free Childcare through caring or incapacity"
    documentation = (
        "Whether regulation 13 of the Childcare Payments (Eligibility) "
        "Regulations 2015 regards this person as in paid work, with expected "
        "income equal to the minimum weekly income. It applies while the "
        "person receives a caring or incapacity benefit (reg 13(1)(b)-(c)) "
        "and has a partner in qualifying paid work (reg 13(1)(a)). The partner "
        "does not count as in qualifying paid work while they receive such a "
        "benefit themselves (reg 13(3)). A lone parent cannot qualify this "
        "way. The partner's own minimum income is tested by the income "
        "condition."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/13"

    def formula(person, period, parameters):
        claimant_or_partner = person("is_claimant_or_partner", period)
        caring_or_incapacity = person(
            "tax_free_childcare_caring_or_incapacity_benefit", period
        )
        # Reg 13(1)(a) and (3): in paid work, and not paid or entitled to a
        # caring or incapacity benefit.
        in_work_without_caring_or_incapacity = (
            claimant_or_partner
            & person("tax_free_childcare_treated_as_in_work", period)
            & ~caring_or_incapacity
        )
        partner_in_qualifying_paid_work = (
            person.benunit.sum(in_work_without_caring_or_incapacity)
            - in_work_without_caring_or_incapacity
        ) > 0
        return (
            claimant_or_partner & caring_or_incapacity & partner_in_qualifying_paid_work
        )
