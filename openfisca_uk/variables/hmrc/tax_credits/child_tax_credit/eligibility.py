from openfisca_uk.model_api import *


class is_child_for_ctc(Variable):
    value_type = bool
    entity = Person
    label = "Child eligible for the Child Tax Credit"
    documentation = "Whether this child confers eligibility to the parents for the Child Tax Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/5"

    def formula(person, period):
        return person("is_child_or_QYP", period)


class is_ctc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Child Tax Credit eligibility"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2002/21/section/8"

    def formula(benunit, period):
        return benunit.any(benunit.members("is_child_for_ctc", period))
