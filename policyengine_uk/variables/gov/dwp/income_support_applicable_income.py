from policyengine_uk.model_api import *


class income_support_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Income Support means test"
    documentation = (
        "The claimant's and partner's income for Income Support, including "
        "statutory sick, maternity and paternity pay, spousal maintenance and "
        "tariff income from capital, less income tax, National Insurance, "
        "half of pension contributions, £10 a week of widowed parent's "
        "allowance and the Schedule 8 earnings disregard, which is capped at "
        "net earnings (income_support_earnings_disregard). Child maintenance "
        "is disregarded."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/8",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/36",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/38",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/35",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/40",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/1",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/4",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/15",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/16",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9/paragraph/73",
    )

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant and partner (IS Regs 1987
        # reg 23(1)). The income of a child or young person in the claimant's
        # family "shall not be treated as the income or capital of the
        # claimant" (reg 23(2)). Anyone else in the benefit unit does not count
        # either.
        person = benunit.members
        members = person("is_claimant_or_partner", period)
        IS = parameters(period).gov.dwp.income_support
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "property_income_after_finance_costs",
            "private_pension_income",
            # Employer statutory pay counts as other income (reg 40(4)(a)).
            "statutory_sick_pay",
            "statutory_maternity_pay",
            "statutory_paternity_pay",
            # Reg 40 and Sch 9 para 15(3)(a): spousal maintenance is
            # non-earnings income, even when paid voluntarily. Child
            # maintenance (maintenance_income) is disregarded by para 73.
            "spousal_maintenance_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            INCOME_COMPONENTS.append("basic_income")
        income = add_for_members(benunit, period, INCOME_COMPONENTS, members)
        tax = add_for_members(
            benunit,
            period,
            ["income_tax_before_winter_fuel_payment_charge", "national_insurance"],
            members,
        )
        income += add_for_members(benunit, period, ["social_security_income"], members)
        # IS Regs 1987 Sch 9 para 16(h): £10 a week of widowed parent's
        # allowance is disregarded; social_security_income counts it in full.
        # Not modelled: paras 36 and 37, which limit this and the war
        # pension disregards together.
        wpa_disregard = (
            IS.means_test.widowed_parents_allowance_disregard * WEEKS_IN_YEAR
        )
        income -= benunit.sum(
            min_(person("widowed_parents_allowance", period), wpa_disregard) * members
        )
        income += benunit("income_support_tariff_income", period)
        income -= tax
        # IS Regs 1987 reg 36(3)(b) and reg 38(1)(b)(ii), (3)(c) and (9)(b).
        income -= (
            add_for_members(benunit, period, ["pension_contributions"], members)
            * IS.means_test.pension_contribution_deduction_rate
        )
        # Schedule 8 disregards earnings only (regs 36(2) and 38(2)), so the
        # disregard is capped at the claimant's and partner's net earnings.
        # Statutory pay, pensions, benefits and maintenance are income other
        # than earnings (reg 40) and keep no part of it.
        return max_(0, income - benunit("income_support_earnings_disregard", period))
