from policyengine_uk.model_api import *


class receives_uc_carer_element(Variable):
    value_type = bool
    entity = Person
    label = "receives the Universal Credit carer element"
    documentation = (
        "Whether this person is a claimant who is a carer, in a benefit unit "
        "whose Universal Credit award includes the carer element (Universal "
        "Credit Regulations 2013 reg 29). The carer element is a benefit-unit "
        "amount; this attributes it to the carer, and requires an award, "
        "since uc_carer_element is calculated whether or not there is one. "
        "The element is for a claimant (reg 29(1)), so a child or qualifying "
        "young person who cares does not receive it. Where both joint "
        "claimants are carers with limited capability for work and "
        "work-related activity, the award has one carer element (reg 29(4)) "
        "and the model does not say whose, so it attributes it to both."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/29"

    def formula(person, period, parameters):
        benunit = person.benunit
        award_includes_carer_element = (benunit("universal_credit", period) > 0) & (
            benunit("uc_carer_element", period) > 0
        )
        claimant_carer = person("is_uc_single_or_joint_claimant", period) & person(
            "is_carer_for_benefits", period
        )
        return claimant_carer & award_includes_carer_element
