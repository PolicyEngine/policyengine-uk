from policyengine_uk.model_api import *


class tax_credits_current_year_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Current year income for Tax Credits"
    documentation = (
        "The claimant's, or joint claimants', income for the tax year "
        "(TCA 2002 s.7(4); SI 2002/2006 reg 3), before TCA 2002 s.7(2) lifts "
        "the income test for a claimant on a prescribed benefit. The model "
        "takes it as the relevant income (s.7(3)). The income test reads "
        "tax_credits_applicable_income, which is nil while the test is "
        "lifted; the targeted childcare criteria read this gross figure."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/21/section/7",
        "https://www.legislation.gov.uk/uksi/2002/2006/regulation/3",
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
        return income
