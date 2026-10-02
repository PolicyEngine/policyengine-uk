from policyengine_uk.model_api import *


class pension_credit_earnings_disregard(Variable):
    label = "Pension Credit earnings disregard"
    documentation = (
        "Earnings disregarded from Pension Credit income under Schedule VI to "
        "the State Pension Credit Regulations 2002: 20 pounds a week for a "
        "lone parent (para. 1), where the claimant or partner is a carer "
        "satisfying Sch. I para. 4 (para. 3), or where the claimant or partner "
        "receives a listed disability benefit or is certified blind "
        "(para. 4(1)); otherwise 5 pounds a week for a single claimant and 10 "
        "pounds for a couple (para. 5). 20 pounds is the most disregarded "
        "however many conditions are met (para. 4A), and the disregard never "
        "exceeds the earnings. Not modelled: the employment-specific 20 pound "
        "disregards of paras. 2 to 2B (part-time firefighters, auxiliary "
        "coastguards, lifeboat crew, reserve forces) and the transitional "
        "protections of para. 4(2) to (4)."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.earnings_disregard
        person = benunit.members
        claimant_or_partner = person("is_uc_claimant", period)
        on_disability_benefit = (
            add(person, period, p.higher.disability_benefits) > 0
        ) | person("is_blind", period)
        unit_disability_benefits = p.higher.disability_benefit_unit_benefits
        unit_on_disability_benefit = (
            add(benunit, period, unit_disability_benefits) > 0
            if len(unit_disability_benefits) > 0
            else False
        )
        disabled = (
            benunit.any(claimant_or_partner & on_disability_benefit)
            | unit_on_disability_benefit
        )
        carer = benunit("carer_minimum_guarantee_addition", period) > 0
        lone_parent = benunit("is_lone_parent", period)
        relation_type = benunit("relation_type", period)
        weekly = where(
            lone_parent | carer | disabled,
            p.higher.amount,
            p.standard[relation_type],
        )
        earnings = max_(0, benunit("pension_credit_earnings", period))
        return min_(weekly * WEEKS_IN_YEAR, earnings)
