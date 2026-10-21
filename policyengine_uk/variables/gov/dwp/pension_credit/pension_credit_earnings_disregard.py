from policyengine_uk.model_api import *


class pension_credit_earnings_disregard(Variable):
    label = "Pension Credit earnings disregard"
    documentation = (
        "Earnings disregarded from Pension Credit income under Schedule VI to "
        "the State Pension Credit Regulations 2002: 20 pounds a week for a "
        "lone parent (para. 1), where the claimant or partner is a carer "
        "satisfying Sch. I para. 4 (para. 3), or where the claimant or partner "
        "receives a listed disability benefit (including working tax credit "
        "with its disability or severe disability element) or is certified "
        "blind (para. 4(1)); otherwise 5 pounds a week for a single claimant and 10 "
        "pounds for a couple (para. 5). 20 pounds is the most disregarded "
        "however many conditions are met (para. 4A). Reg. 17(9) disregards the "
        "sums 'in calculating the claimant's earnings', which are net of income "
        "tax and National Insurance (reg. 17(10)) and of half of pension "
        "contributions (reg. 17A(4A)), so the disregard never exceeds the "
        "claimant's and partner's net earnings, each source floored at nil. "
        "Employed earnings (regs. 17(10) and 17A) are net of primary Class 1 "
        "contributions and of the income tax payable on them "
        "(pension_credit_employment_income_tax). Self-employed earnings (regs. "
        "17(11) and 17B) are net of the notional tax and contributions of the "
        "Computation of Earnings Regulations 1996 reg. 14 "
        "(pension_credit_self_employment_deductions). Half of pension "
        "contributions come off both. Not modelled: the employment-specific "
        "20 pound "
        "disregards of paras. 2 to 2B (part-time firefighters, auxiliary "
        "coastguards, lifeboat crew, reserve forces) and the transitional "
        "protections of para. 4(2) to (4), and the continued carer "
        "qualification of Sch. I para. 4 after carer's allowance stops (the "
        "model has no record of when it stopped). The carer condition reads "
        "is_entitled_to_carer_benefit, the carer addition's own test, so the "
        "two always agree; the Carer's Allowance earnings limit is applied to "
        "that test by PolicyEngine/policyengine-uk#2312."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17A",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17B",
        "https://www.legislation.gov.uk/uksi/1996/2745/regulation/13",
        "https://www.legislation.gov.uk/uksi/1996/2745/regulation/14",
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
        # Para. 4(1)(a)(vi): in receipt of working tax credit that includes
        # its disability or severe disability element.
        wtc_disability_element = (
            add(
                benunit,
                period,
                ["WTC_disabled_element", "WTC_severely_disabled_element"],
            )
            > 0
        ) & (benunit("working_tax_credit", period) > 0)
        disabled = (
            benunit.any(claimant_or_partner & on_disability_benefit)
            | unit_on_disability_benefit
            | wtc_disability_element
        )
        # Sch. I para. 4: a claimant or partner entitled to carer's allowance
        # (the carer addition's own test), not caring hours alone.
        carer = benunit.any(
            claimant_or_partner & person("is_entitled_to_carer_benefit", period)
        )
        lone_parent = benunit("is_lone_parent", period)
        relation_type = benunit("relation_type", period)
        weekly = where(
            lone_parent | carer | disabled,
            p.higher.amount,
            p.standard[relation_type],
        )

        # Net earnings of the claimant and partner, each source floored at
        # nil: a loss in one employment is not set against another (CER 1996
        # reg. 13(12), applied by SPC Regs 2002 reg. 17B).
        # Employed earners (regs. 17(10) and 17A): less the income tax payable
        # on the earnings and the primary Class 1 contributions deducted from
        # them. Self-employed earners (regs. 17(11) and 17B): less the
        # notional tax and contributions of CER 1996 regs. 13(4) and 14. Both:
        # less half of pension contributions (reg. 17A(4A); CER 1996 reg.
        # 13(4)(c)).
        employment = max_(0, person("employment_income", period))
        self_employment = max_(0, person("self_employment_income", period))
        deductions = add(
            person,
            period,
            ["ni_class_1_employee", "pension_credit_self_employment_deductions"],
        ) + (
            person("pension_contributions", period)
            * pc.income.pension_contributions_deduction
        )
        # Each person's deductions come off their own earnings; the income tax
        # on employed earnings is measured for the claimant and partner
        # together (pension_credit_employment_income_tax).
        own_net = max_(0, employment + self_employment - deductions)
        net_earnings = max_(
            0,
            benunit.sum(own_net * claimant_or_partner)
            - benunit("pension_credit_employment_income_tax", period),
        )
        return min_(weekly * WEEKS_IN_YEAR, net_earnings)
