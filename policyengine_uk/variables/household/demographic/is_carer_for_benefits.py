from policyengine_uk.model_api import *


class is_carer_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a carer for benefits purposes"
    definition_period = YEAR

    documentation = (
        "Receives a carer benefit, or provides at least the Carer's Allowance "
        "qualifying hours of care a week (regular and substantial caring, "
        "which the Universal Credit carer element and the legacy carer "
        "premiums recognise without a Carer's Allowance award)."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/30"

    def formula(person, period, parameters):
        min_hours = parameters(period).gov.dwp.carers_allowance.min_hours
        meets_hours = person("care_hours", period) >= min_hours
        return person("receives_carer_benefit", period) | meets_hours
