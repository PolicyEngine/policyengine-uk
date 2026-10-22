from policyengine_uk.model_api import *


class pension_credit_income(Variable):
    label = "Income for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/5",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/15",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
    )
    documentation = (
        "Income and deductions of the claimant and partner, together with "
        "benefit-unit income sources. Dependants' income and deductions "
        "are excluded."
    )

    def formula(benunit, period, parameters):
        pc = parameters(period).gov.dwp.pension_credit
        sources = pc.guarantee_credit.income
        person = benunit.members
        is_claimant_or_partner = person("is_claimant_or_partner", period)
        total = 0
        for source in sources:
            if person.entity.get_variable(source).entity.is_person:
                # Nothing in the State Pension Credit Act 2002 ss. 15 to 16
                # or SPC Regs 2002 regs. 15 to 18 lets a loss on one source
                # be set against another, so a negative source, such as a
                # property loss, counts as nil.
                total += benunit.sum(
                    max_(0, person(source, period)) * is_claimant_or_partner
                )
            else:
                total += add(benunit, period, [source])

        # Benefit-unit sources (pension_credit_earnings, which already counts
        # only the claimant and partner, working tax credit and tariff income)
        # are counted once.
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            total += benunit.sum(
                person("basic_income", period) * is_claimant_or_partner
            )
        pension_contributions = benunit.sum(
            person("pension_contributions", period) * is_claimant_or_partner
        )
        # Self-employed earnings are net of the notional tax and contributions
        # of the Computation of Earnings Regulations 1996 reg. 14, in place of
        # those actually payable on the profit (reg. 17(11)).
        tax = benunit.sum(
            (
                add(
                    person,
                    period,
                    [
                        "income_tax",
                        "national_insurance",
                        "pension_credit_self_employment_deductions",
                    ],
                )
                - add(person, period, ["ni_class_2", "ni_class_4"])
            )
            * is_claimant_or_partner
        ) - benunit("pension_credit_self_employment_income_tax", period)
        pen_con_deduction_rate = pc.income.pension_contributions_deduction
        deductions = tax + pension_contributions * pen_con_deduction_rate
        # Schedule VI earnings disregards (reg. 17(9)).
        earnings_disregard = benunit("pension_credit_earnings_disregard", period)
        return max_(0, total - deductions - earnings_disregard)
