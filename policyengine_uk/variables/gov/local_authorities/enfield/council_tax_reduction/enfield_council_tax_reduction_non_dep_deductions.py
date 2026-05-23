from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_enfield_working_age,
)


class enfield_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Enfield CTR non-dependent deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.enfield.council_tax_reduction
        working_age = is_enfield_working_age(
            benunit.household("local_authority", period),
            benunit.household("country", period),
            benunit.household("council_tax_reduction_household_has_pensioner", period),
        )
        person = benunit.members
        eligible = person(
            "council_tax_reduction_individual_non_dep_deduction_eligible",
            period,
        )
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        exempt = child_or_young_person | is_full_time_student_non_dep(person, period)
        countable = eligible & ~exempt
        gross_earnings = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_gross_earnings = benunit.sum(countable * gross_earnings) / WEEKS_IN_YEAR
        deduction_for_benunit = where(
            benunit.any(countable),
            ctr.non_dep_deduction.amount.calc(weekly_gross_earnings) * WEEKS_IN_YEAR,
            0,
        )
        is_benunit_head = person("is_benunit_head", period)
        deductions_to_count = is_benunit_head * benunit.project(deduction_for_benunit)
        deductions_in_household = benunit.max(
            benunit.members.household.sum(deductions_to_count)
        )
        return working_age * (deductions_in_household - deduction_for_benunit)
