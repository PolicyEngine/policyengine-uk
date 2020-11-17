from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class BSP(Variable):
    value_type = float
    entity = Person
    label = u'Bereavement Support Payment'
    definition_period = MONTH

class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = u'Employment and Support Allowance (contribution-based)'
    definition_period = WEEK

class JSA_contrib(Variable):
    value_type = float
    entity = Person
    label = u'Job Seeker\'s Allowance (contribution-based)'
    definition_period = WEEK

class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Carer\'s Allowance'
    definition_period = WEEK