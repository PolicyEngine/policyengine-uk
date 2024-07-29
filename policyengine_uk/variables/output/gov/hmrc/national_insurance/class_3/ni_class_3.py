from policyengine_uk.model_api import *


class ni_class_3(Variable):
    label = "NI Class 3 contributions"
    documentation = "Voluntary contributions to NI."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "ni_liable"
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/13"
