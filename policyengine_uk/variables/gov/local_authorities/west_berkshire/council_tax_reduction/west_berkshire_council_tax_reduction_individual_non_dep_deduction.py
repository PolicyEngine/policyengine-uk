from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


# Paragraph 30 of the West Berkshire scheme mirrors the prescribed Default Scheme
# non-dependant deduction schedule. The 2026/27 amounts published by the scheme
# are GBP 15.95 / GBP 13.30 / GBP 10.60 / GBP 5.20 across the four prescribed
# remunerative-work income brackets.
_2026_BRACKETS = [
    (0.0, 5.20),
    (279.0, 10.60),
    (485.0, 13.30),
    (605.0, 15.95),
]
_NON_WORK_RATE = 5.20


class west_berkshire_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "West Berkshire Council Tax Reduction individual non-dependant deduction"
    documentation = "Paragraph 30 applies the prescribed Default Scheme non-dependant deduction schedule. Sub-paragraph (1)(a) sets the in-remunerative-work deduction at 15.95 pounds weekly, and sub-paragraph (1)(b) sets the out-of-work deduction at 5.20 pounds weekly. Sub-paragraph (2) overrides the in-work amount with 5.20/10.60/13.30 pounds for normal gross weekly income below 279, 485 and 605 pounds respectively. Paragraph 30(6)-(8) lists the same exemptions as the prescribed Default Scheme."
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = "https://www.westberks.gov.uk/media/66425/Council-Tax-Reduction-Scheme-2026-27/pdf/The_Council_Tax_Reduction_Scheme_as_amended_by_West_Berkshire_Council_2026.pdf"

    def formula(person, period, parameters):
        household = person.household
        local_scheme = household.any(
            person.benunit("benunit_contains_household_head", period)
            & person.benunit(
                "west_berkshire_council_tax_reduction_is_local_scheme", period
            )
        )
        gross_income_components = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "private_pension_income",
            "savings_interest_income",
            "dividend_income",
            "state_pension",
        ]
        gross_income = add(person, period, gross_income_components)
        weekly_benunit_gross_income = person.benunit.sum(gross_income) / WEEKS_IN_YEAR
        benunit_weekly_hours = person.benunit.max(person("weekly_hours", period))
        in_remunerative_work = benunit_weekly_hours >= 16
        # Build the bracket lookup as a select cascade for clarity.
        weekly_amount = where(
            weekly_benunit_gross_income >= _2026_BRACKETS[3][0],
            _2026_BRACKETS[3][1],
            where(
                weekly_benunit_gross_income >= _2026_BRACKETS[2][0],
                _2026_BRACKETS[2][1],
                where(
                    weekly_benunit_gross_income >= _2026_BRACKETS[1][0],
                    _2026_BRACKETS[1][1],
                    _2026_BRACKETS[0][1],
                ),
            ),
        )
        weekly_deduction = where(in_remunerative_work, weekly_amount, _NON_WORK_RATE)
        # Standard prescribed exemptions: applicant blind/AA/PIP/AFIP exemption,
        # full-time-student non-dep, income-based-benefit non-dep, UC-no-earned-income non-dep.
        claimant_exempt = person.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        full_time_student = is_full_time_student_non_dep(person, period)
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        has_uc = person.benunit("universal_credit", period) > 0
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_benunit_earned_income = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
        uc_no_earned_income = has_uc & (weekly_benunit_earned_income <= 0)
        exempt = (
            claimant_exempt
            | full_time_student
            | income_based_benefit
            | uc_no_earned_income
        )
        return local_scheme * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
