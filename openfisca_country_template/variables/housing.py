# -*- coding: utf-8 -*-

# This file defines variables for the modelled legislation.
# A variable is a property of an Entity such as a Person, a Household…
# See https://openfisca.org/doc/key-concepts/variables.html

# Import from openfisca-core the common Python objects used to code the legislation in OpenFisca
from openfisca_core.model_api import *
# Import the Entities specifically defined for this tax and benefit system
from openfisca_country_template.entities import *


# This variable is a pure input: it doesn't have a formula
class accommodation_size(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    label = u"Size of the accommodation, in square metres"


# This variable is a pure input: it doesn't have a formula
class rent(Variable):
    value_type = float
    entity = Household
    definition_period = MONTH
    label = u"Rent paid by the household"


# Possible values for the housing_occupancy_status variable, defined further down
# See more at <https://openfisca.org/doc/coding-the-legislation/20_input_variables.html#advanced-example-enumerations-enum>
class HousingOccupancyStatus(Enum):
    __order__ = "owner tenant free_lodger homeless"
    owner = u'Owner'
    tenant = u'Tenant'
    free_lodger = u'Free lodger'
    homeless = u'Homeless'


class housing_occupancy_status(Variable):
    value_type = Enum
    possible_values = HousingOccupancyStatus
    default_value = HousingOccupancyStatus.tenant
    entity = Household
    definition_period = MONTH
    label = u"Legal housing situation of the household concerning their main residence"


class postal_code(Variable):
    value_type = str
    max_length = 5
    entity = Household
    definition_period = MONTH
    label = "Postal code of the household"
