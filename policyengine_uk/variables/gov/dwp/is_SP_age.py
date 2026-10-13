from policyengine_uk.model_api import *


class is_SP_age(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is State Pension Age"
    documentation = (
        "Whether the person has attained State Pension age by the middle of "
        "the fiscal year (6 October), so is over it for most of the year."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/1995/26/schedule/4"

    def formula(person, period, parameters):
        return person("months_since_state_pension_age", period) >= 0
