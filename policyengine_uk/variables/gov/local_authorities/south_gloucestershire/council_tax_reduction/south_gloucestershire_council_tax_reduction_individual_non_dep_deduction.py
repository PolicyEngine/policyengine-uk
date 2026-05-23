from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class south_gloucestershire_council_tax_reduction_individual_non_dep_deduction(
    Variable
):
    value_type = float
    entity = Person
    label = "South Gloucestershire CTR individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf"

    def formula(person, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.south_gloucestershire.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "south_gloucestershire_council_tax_reduction_is_local_scheme",
                period,
            )
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | person.benunit.any(
                person(
                    "south_gloucestershire_council_tax_reduction_non_dep_guarantee_credit",
                    period,
                )
            )
        )
        maximum_uc = (
            max_(
                person.benunit("universal_credit_pre_benefit_cap", period),
                person.benunit("universal_credit", period),
            )
            > 0
        ) & (
            person.benunit("universal_credit_pre_benefit_cap", period)
            >= person.benunit("uc_maximum_amount", period)
        )
        remunerative_work = (
            person("weekly_hours", period)
            >= ctr.non_dep_deduction.remunerative_work_hours
        )
        low_deduction = (
            income_based_benefit
            | maximum_uc
            | ~remunerative_work
            | is_full_time_student_non_dep(person, period)
        )
        weekly_deduction = where(
            low_deduction,
            ctr.non_dep_deduction.low_amount,
            ctr.non_dep_deduction.high_amount,
        )
        source_exempt = person(
            "south_gloucestershire_council_tax_reduction_non_dep_source_exemption",
            period,
        )
        return local_scheme * where(
            source_exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR
        )
