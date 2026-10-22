from policyengine_uk.model_api import *


class income_support_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Income Support means test"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/8",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/36",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/38",
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
        income += benunit("income_support_tariff_income", period)
        income -= tax
        # IS Regs 1987 reg 36(3)(b) and reg 38(1)(b)(ii), (3)(c) and (9)(b).
        income -= (
            add_for_members(benunit, period, ["pension_contributions"], members)
            * IS.means_test.pension_contribution_deduction_rate
        )
        # Schedule 8 paras 5, 6 and 10 use mutually exclusive claimant types.
        mt = IS.means_test
        single = benunit("is_single_person", period)
        income_disregard_single = single * mt.income_disregard_single
        income_disregard_couple = (
            benunit("is_couple", period) * mt.income_disregard_couple
        )
        lone_parent = benunit("is_lone_parent", period)
        income_disregard_lone_parent = lone_parent * mt.income_disregard_lone_parent
        income_disregard = (
            income_disregard_single
            + income_disregard_couple
            + income_disregard_lone_parent
        ) * WEEKS_IN_YEAR
        return max_(0, income - income_disregard)
