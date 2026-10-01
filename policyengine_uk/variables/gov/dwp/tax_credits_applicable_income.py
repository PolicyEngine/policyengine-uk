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
        # Members whose income counts: the claimant and partner and, as the model did
        # before, the programme's own children or young persons. The regulations count
        # only the claimant's and partner's (TCA 2002 s.7); dropping dependants' own
        # income is a follow-up. Anyone else in the benefit unit does not count.
        person = benunit.members
        members = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        TC = parameters(period).gov.dwp.tax_credits
        STEP_1_COMPONENTS = [
            "private_pension_income",
            "savings_interest_income",
            "dividend_income",
            "property_income",
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
