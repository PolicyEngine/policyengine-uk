from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_derby_working_age,
)


class derby_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Derby Council Tax Support individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = "https://www.derby.gov.uk/media/derbycitycouncil/contentassets/documents/adviceandbenefits/counciltax/council-tax-support-scheme2026-27.pdf"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.derby.council_tax_reduction
        household = person.household
        working_age = is_derby_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        gross_income = earned_income + add(
            person,
            period,
            [
                "property_income",
                "private_pension_income",
                "savings_interest_income",
                "dividend_income",
                "state_pension",
            ],
        )
        weekly_gross_income = person.benunit.sum(gross_income) / WEEKS_IN_YEAR
        weekly_earned_income = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
        is_remunerative_work = person.benunit.max(person("weekly_hours", period)) >= 16
        has_uc_award = person.benunit("universal_credit", period) > 0
        passport_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        derby_low_deduction = (
            is_remunerative_work
            & (weekly_gross_income < ctr.non_dep_deduction.low_income_threshold)
        ) | (~is_remunerative_work & (has_uc_award | passport_benefit))
        weekly_deduction = where(
            derby_low_deduction,
            ctr.non_dep_deduction.low_amount,
            where(
                is_remunerative_work,
                ctr.non_dep_deduction.amount.calc(weekly_gross_income),
                ctr.non_dep_deduction.amount.calc(0),
            ),
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        exempt = claimant_exempt | is_full_time_student_non_dep(person, period)
        return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
