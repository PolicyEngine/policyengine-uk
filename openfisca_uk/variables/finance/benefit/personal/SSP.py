from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class SSP_reported(Variable):
	value_type = float
	entity = Person
	label = u'Statutory Sick Pay'
	definition_period = YEAR