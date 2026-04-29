from policyengine_uk.model_api import *


class is_child_or_qualifying_young_person_for_child_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Child or qualifying young person for Child Benefit"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/ukpga/1992/4/section/142",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/143",
        "https://www.legislation.gov.uk/uksi/2006/223",
    ]

    def formula(person, period, parameters):
        return person("is_child_for_child_benefit", period) | person(
            "is_qualifying_young_person_for_child_benefit", period
        )
