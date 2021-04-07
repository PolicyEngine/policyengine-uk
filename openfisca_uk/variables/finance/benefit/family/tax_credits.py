from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit (reported amount)"
    definition_period = WEEK


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit (reported amount)"
    definition_period = WEEK