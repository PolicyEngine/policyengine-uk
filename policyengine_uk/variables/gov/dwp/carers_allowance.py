from policyengine_uk.model_api import *


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"
        csp_replaces_ca = period.start.year >= 2025
        receives_ca = person("carers_allowance_reported", period) > 0
        ca = parameters(period).gov.dwp.carers_allowance
        weekly_care_hours = person("care_hours", period)
        meets_work_condition = weekly_care_hours >= ca.min_hours
        eligible = ~(in_scotland & csp_replaces_ca) & (
            meets_work_condition | receives_ca
        )
        return eligible * ca.rate * WEEKS_IN_YEAR
