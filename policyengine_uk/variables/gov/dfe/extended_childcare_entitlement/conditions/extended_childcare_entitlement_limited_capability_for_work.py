from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import is_supplied_input


class extended_childcare_entitlement_limited_capability_for_work(Variable):
    value_type = bool
    entity = Person
    label = "Supplied current limited capability for work for extended childcare"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/4",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/14",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/15",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/39",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/40",
    )

    def formula(person, period, parameters):
        lcw = person("uc_limited_capability_for_work", period)
        lcwra = person("uc_limited_capability_for_WRA", period)
        return (
            lcw
            & is_supplied_input(person, "uc_limited_capability_for_work", period, lcw)
        ) | (
            lcwra
            & is_supplied_input(person, "uc_limited_capability_for_WRA", period, lcwra)
        )
