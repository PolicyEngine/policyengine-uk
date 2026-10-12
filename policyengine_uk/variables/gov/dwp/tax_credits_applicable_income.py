from policyengine_uk.model_api import *


class tax_credits_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable income for Tax Credits"
    definition_period = YEAR
    unit = GBP
    reference = (
        "The Tax Credits (Definition and Calculation of Income) Regulations 2002 s. 3"
    )

    def formula(benunit, period, parameters):
        # Members whose income counts: the claimant or, on a joint claim, the
        # claimants (TCA 2002 s.7; Tax Credits (Definition and Calculation of
        # Income) Regs 2002 reg 3(1)). A child's or qualifying young person's
        # own income does not count, nor anyone else's in the benefit unit.
        person = benunit.members
        members = person("is_claimant_or_partner", period)
        TC = parameters(period).gov.dwp.tax_credits
        STEP_1_COMPONENTS = [
            "private_pension_income",
            "savings_interest_income",
            "dividend_income",
            "property_income_after_finance_costs",
        ]
        income = add_for_members(benunit, period, STEP_1_COMPONENTS, members)
        income = max_(income - TC.means_test.non_earned_disregard, 0)
        STEP_2_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "social_security_income",
            "miscellaneous_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            STEP_2_COMPONENTS.append("basic_income")
        income += add_for_members(benunit, period, STEP_2_COMPONENTS, members)
        # TCA 2002 s.7(2) and SI 2002/2008 reg 4: no income test while "the
        # person, or either of the persons" claiming is entitled to Income
        # Support, income-based JSA or income-related ESA. That is the claimant's
        # or partner's award, not another member's.
        EXEMPT_BENEFITS = [
            "income_support",
            "claimant_or_partner_esa_income",
            "claimant_or_partner_jsa_income",
        ]
        on_exempt_benefits = (
            add_for_members(benunit, period, EXEMPT_BENEFITS, members) > 0
        )
        return income * ~on_exempt_benefits
