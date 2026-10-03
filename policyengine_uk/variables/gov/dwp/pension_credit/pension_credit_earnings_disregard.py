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
        "however many conditions are met (para. 4A). Reg. 17(9) disregards the "
        "sums 'in calculating the claimant's earnings', which are net of income "
        "tax and National Insurance (reg. 17(10)) and of half of pension "
        "contributions (reg. 17A(4A)), so the disregard never exceeds the "
        "claimant's and partner's net earnings. Income tax on earnings is taken "
        "as the lesser of the person's income tax and the basic rate on their "
        "earnings, the tax deducted where the personal allowance goes against "
        "pension income first. Not modelled: the employment-specific 20 pound "
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
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17A",
    )

    def formula(benunit, period, parameters):
        pc = parameters(period).gov.dwp.pension_credit
        p = pc.earnings_disregard
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)

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
        # Sch. I para. 4: a claimant or partner entitled to carer's allowance.
        carer = benunit.any(
            claimant_or_partner & person("is_carer_for_benefits", period)
        )
        lone_parent = benunit("is_lone_parent", period)
        relation_type = benunit("relation_type", period)
        weekly = where(
            lone_parent | carer | disabled,
            p.higher.amount,
            p.standard[relation_type],
        )

        # Net earnings of the claimant and partner (regs. 17(10), 17A(4A)).
        gross = max_(0, add(person, period, pc.guarantee_credit.earnings_sources))
        national_insurance = add(
            person, period, ["ni_class_1_employee", "ni_class_2", "ni_class_4"]
        )
        basic_rate = parameters(period).gov.hmrc.income_tax.rates.uk.rates[0]
        income_tax_on_earnings = min_(person("income_tax", period), basic_rate * gross)
        pension_contributions = (
            person("pension_contributions", period)
            * pc.income.pension_contributions_deduction
        )
        net = max_(
            0,
            gross - national_insurance - income_tax_on_earnings - pension_contributions,
        )
        net_earnings = benunit.sum(net * claimant_or_partner)
        return min_(weekly * WEEKS_IN_YEAR, net_earnings)
