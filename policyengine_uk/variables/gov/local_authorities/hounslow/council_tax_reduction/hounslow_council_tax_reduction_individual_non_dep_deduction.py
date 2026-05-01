from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_hounslow_working_age,
)


class hounslow_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Hounslow CTS individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.hounslow.council_tax_reduction
        household = person.household
        working_age = is_hounslow_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        remunerative_work = (
            person("weekly_hours", period)
            >= ctr.non_dep_deduction.remunerative_work_hours
        )
        weekly_deduction = where(
            remunerative_work,
            ctr.non_dep_deduction.working_amount,
            ctr.non_dep_deduction.non_working_amount,
        )
        return working_age * weekly_deduction * WEEKS_IN_YEAR
