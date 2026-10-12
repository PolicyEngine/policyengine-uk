from policyengine_uk.model_api import *


class receives_uc_carer_element(Variable):
    value_type = bool
    entity = Person
    label = "receives the Universal Credit carer element"
    documentation = (
        "Whether this person is a claimant in respect of whom the Universal "
        "Credit award includes the carer element (Universal Credit "
        "Regulations 2013 reg 29; `uc_carer_element_included_for_claimant`), "
        "on an award. The carer element is a benefit-unit amount; this "
        "attributes it to the claimant it is included for, and requires an "
        "award, since uc_carer_element is calculated whether or not there is "
        "one. A child or qualifying young person who cares does not receive "
        "it, nor does a carer who has only the LCWRA element (reg 29(4))."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/29"

    def formula(person, period, parameters):
        benunit = person.benunit
        award_includes_carer_element = (benunit("universal_credit", period) > 0) & (
            benunit("uc_carer_element", period) > 0
        )
        included_for_this_claimant = person(
            "uc_carer_element_included_for_claimant", period
        )
        return included_for_this_claimant & award_includes_carer_element
