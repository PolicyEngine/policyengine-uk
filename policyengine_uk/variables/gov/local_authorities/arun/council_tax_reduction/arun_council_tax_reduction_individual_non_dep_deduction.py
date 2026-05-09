from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class arun_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Arun Council Tax Reduction individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.arun.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "arun_council_tax_reduction_is_local_scheme",
                period,
            )
        )
        person_income = add(
            person,
            period,
            [
                "employment_income",
                "self_employment_income",
                "property_income",
                "private_pension_income",
                "maintenance_income",
                "savings_interest_income",
                "dividend_income",
                "state_pension",
                "miscellaneous_income",
                "carers_allowance",
                "attendance_allowance",
                "dla",
                "pip",
                "armed_forces_independence_payment",
                "universal_credit_reported",
            ],
        )
        benunit_income = add(
            person.benunit,
            period,
            [
                "tax_credits",
                "child_benefit",
                "housing_benefit",
                "income_support",
                "jsa_income",
                "esa_income",
                "pension_credit",
            ],
        )
        no_income = (person_income + benunit_income) <= 0
        in_remunerative_work = (
            person.benunit.max(person("weekly_hours", period))
            >= ctr.non_dep_deduction.remunerative_work_hours
        )
        chargeable = no_income | in_remunerative_work
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | person.benunit.any(
                person("arun_council_tax_reduction_non_dep_guarantee_credit", period)
            )
        )
        receives_universal_credit = person.benunit("universal_credit", period) > 0
        exempt = (
            is_full_time_student_non_dep(person, period)
            | income_based_benefit
            | receives_universal_credit
            | person("arun_council_tax_reduction_non_dep_source_exemption", period)
        )
        return local_scheme * where(
            exempt | ~chargeable, 0.0, ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        )
