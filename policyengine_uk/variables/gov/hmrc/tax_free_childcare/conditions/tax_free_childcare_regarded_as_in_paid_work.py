from policyengine_uk.model_api import *


class tax_free_childcare_regarded_as_in_paid_work(Variable):
    value_type = bool
    entity = Person
    label = "regarded as in qualifying paid work for Tax-Free Childcare through caring or incapacity"
    documentation = (
        "Whether regulation 13 of the Childcare Payments (Eligibility) "
        "Regulations 2015 regards this person as in paid work, with expected "
        "income equal to the minimum weekly income. It applies while the "
        "person receives a caring or incapacity benefit (reg 13(1)(b)) or, "
        "from 6 April 2024, is on carer's leave (reg 13(1)(c)), and has a "
        "partner in qualifying paid work (reg 13(1)(a)). The partner does not "
        "count as in qualifying paid work while they are paid a reg 13(1)(b) "
        "benefit or allowance, or entitled to a reg 13(1)(b) credit (reg "
        "13(3)); entitlement to an allowance reduced to nil by an overlapping "
        "benefit, and carer's leave, do not have that effect. A lone parent cannot qualify this way. The partner's own "
        "minimum income is tested by the income condition."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2015/448/regulation/13"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare
        claimant_or_partner = person("is_claimant_or_partner", period)
        caring_or_incapacity_benefit = person(
            "tax_free_childcare_caring_or_incapacity_benefit", period
        )
        on_qualifying_carers_leave = (
            person("tax_free_childcare_on_carers_leave", period)
            & p.carers_leave_qualifies
        )
        # Reg 13(1)(a) and (3): in paid work, and not paid a reg 13(1)(b)
        # benefit or allowance or entitled to a reg 13(1)(b) credit.
        paid_caring_or_incapacity_benefit = (
            add(person, period, p.caring_or_incapacity_benefits_in_payment) > 0
        )
        in_work_without_caring_or_incapacity_benefit = (
            claimant_or_partner
            & person("tax_free_childcare_treated_as_in_work", period)
            & ~paid_caring_or_incapacity_benefit
        )
        partner_in_qualifying_paid_work = (
            person.benunit.sum(in_work_without_caring_or_incapacity_benefit)
            - in_work_without_caring_or_incapacity_benefit
        ) > 0
        return (
            claimant_or_partner
            & (caring_or_incapacity_benefit | on_qualifying_carers_leave)
            & partner_in_qualifying_paid_work
        )
