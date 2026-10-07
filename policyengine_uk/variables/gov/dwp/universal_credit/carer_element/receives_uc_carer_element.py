from policyengine_uk.model_api import *


class receives_uc_carer_element(Variable):
    value_type = bool
    entity = Person
    label = "receives the Universal Credit carer element"
    documentation = (
        "Whether this person is a carer in a benefit unit whose Universal "
        "Credit award includes the carer element (Universal Credit "
        "Regulations 2013 reg 29). The carer element is a benefit-unit "
        "amount; this attributes it to the carer, and requires an award, "
        "since uc_carer_element is calculated for any benefit unit with a "
        "carer."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/29"

    def formula(person, period, parameters):
        benunit = person.benunit
        award_includes_carer_element = (benunit("universal_credit", period) > 0) & (
            benunit("uc_carer_element", period) > 0
        )
        return person("is_carer_for_benefits", period) & award_includes_carer_element
