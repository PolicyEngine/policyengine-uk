from policyengine_uk.model_api import *


class haringey_council_tax_reduction_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Haringey CTR applicable income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        gross_earnings = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + person("self_employment_income", period)
            )
        )
        earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period) * 0.5
            )
        )
        childcare_deduction = benunit(
            "haringey_council_tax_reduction_childcare_deduction", period
        )
        net_earnings = max_(
            0, gross_earnings - earnings_deductions - childcare_deduction
        )
        other_income = benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "carers_allowance",
                    "esa_contrib",
                    "incapacity_benefit",
                    "jsa_contrib",
                    "state_pension",
                    "maternity_allowance",
                    "statutory_sick_pay",
                    "statutory_maternity_pay",
                    "property_income",
                    "private_pension_income",
                    "maintenance_income",
                    "savings_interest_income",
                    "dividend_income",
                    "miscellaneous_income",
                ],
            )
        )
        tax_credits = benunit("tax_credits", period)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        applicable_income = net_earnings + other_income + tax_credits
        return where(relevant_income_based_benefit, 0, applicable_income)
