from policyengine_uk.model_api import *


class uc_is_child_limit_affected(Variable):
    label = "affected by the UC child limit"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/24A"

    def formula(person, period, parameters):
        return (
            (person("uc_individual_child_element", period) == 0)
            & person("is_child_or_qualifying_young_person_for_universal_credit", period)
            & ~person("is_uc_claimant", period)
            & (person.benunit("universal_credit", period) > 0)
        )
