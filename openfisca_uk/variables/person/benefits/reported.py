from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class PIP_DL(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Daily Living)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class PIP_M(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Mobility)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class BSP(Variable):
    value_type = float
    entity = Person
    label = u"Bereavement Support Payment"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class IIDB(Variable):
    value_type = float
    entity = Person
    label = u"Industrial Injuries Disablement Benefit"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Employment and Support Allowance (contribution-based)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class JSA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Job Seeker's Allowance (contribution-based)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Carer's Allowance"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class incapacity_benefit(Variable):
    value_type = float
    entity = Person
    label = u"Incapacity Benefit"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class SDA(Variable):
    value_type = float
    entity = Person
    label = u"Severe Disablement Allowance"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class AA(Variable):
    value_type = float
    entity = Person
    label = u"Attendance Allowance"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class DLA_M(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (mobility component)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class DLA_SC(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (self-care)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)

class PIP_DL_reported(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Daily Living) (reported)"
    definition_period = WEEK


class PIP_M_reported(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Mobility) (reported)"
    definition_period = WEEK


class BSP_reported(Variable):
    value_type = float
    entity = Person
    label = u"Bereavement Support Payment (reported)"
    definition_period = WEEK


class IIDB_reported(Variable):
    value_type = float
    entity = Person
    label = u"Industrial Injuries Disablement Benefit (reported)"
    definition_period = WEEK


class ESA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Employment and Support Allowance (contribution-based) (reported)"
    definition_period = WEEK


class JSA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Job Seeker's Allowance (contribution-based) (reported)"
    definition_period = WEEK


class carers_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Carer's Allowance (reported)"
    definition_period = WEEK


class incapacity_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Incapacity Benefit (reported)"
    definition_period = WEEK


class SDA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Severe Disablement Allowance (reported)"
    definition_period = WEEK


class AA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Attendance Allowance (reported)"
    definition_period = WEEK


class DLA_M_reported(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (mobility component) (reported)"
    definition_period = WEEK


class DLA_SC_reported(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (self-care) (reported)"
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
