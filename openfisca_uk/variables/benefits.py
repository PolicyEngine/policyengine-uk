from openfisca_core.model_api import *
from openfisca_uk.entities import *

class jsa(Variable):
    value_type = float
    entity = Person
    label = u'JSA amount received per month'
    definition_period = MONTH

class income_support(Variable):
    value_type = float
    entity = Person
    label = u'Income Support amount received per month'
    definition_period = MONTH

class housing_benefit(Variable):
    value_type = float
    entity = Person
    label = u'Housing Benefit amount received per month'
    definition_period = MONTH

class child_benefit(Variable):
    value_type = float
    entity = Person
    label = u'Child Benefit amount received per month'
    definition_period = MONTH

class child_tax_credit(Variable):
    value_type = float
    entity = Person
    label = u'Child Tax Credit amount received per month'
    definition_period = MONTH

class working_tax_credit_childcare(Variable):
    value_type = float
    entity = Person
    label = u'Working Tax Credit (Childcare element) amount received per month'
    definition_period = MONTH

class tax_free_childcare(Variable):
    value_type = float
    entity = Person
    label = u'Tax-Free Childcare amount received per month'
    definition_period = MONTH

class working_tax_credit(Variable):
    value_type = float
    entity = Person
    label = u'Working Tax Credit amount received per month'
    definition_period = MONTH