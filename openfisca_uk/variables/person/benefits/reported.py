from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class BSP(Variable):
    value_type = float
    entity = Person
    label = u"Bereavement Support Payment"
    definition_period = WEEK


class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Employment and Support Allowance (contribution-based)"
    definition_period = WEEK


class JSA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Job Seeker's Allowance (contribution-based)"
    definition_period = WEEK


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Carer's Allowance"
    definition_period = WEEK


class incapacity_benefit(Variable):
    value_type = float
    entity = Person
    label = u"Incapacity Benefit"
    definition_period = WEEK


class SDA(Variable):
    value_type = float
    entity = Person
    label = u"Severe Disablement Allowance"
    definition_period = WEEK


class AA(Variable):
    value_type = float
    entity = Person
    label = u"Attendance Allowance"
    definition_period = WEEK


class DLA_M(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (mobility component)"
    definition_period = WEEK


class DLA_SC(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (self-care)"
    definition_period = WEEK


class personal_benefits(Variable):
    value_type = float
    entity = Person
    label = u"Personal, non-means-tested benefits"
    definition_period = WEEK

    def formula(person, period, parameters):
        BENEFITS = [
            "DLA_SC",
            "DLA_M",
            "AA",
            "SDA",
            "incapacity_benefit",
            "carers_allowance",
            "BSP",
            "JSA_contrib",
            "ESA_contrib",
        ]
        return add(person, period, BENEFITS)
