from openfisca_uk.model_api import *


class stamp_duty_on_residential_property(Variable):
    label = "Stamp Duty on residential property"
    documentation = (
        "Tax charge from purchase or rental of residential property"
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class stamp_duty_on_non_residential_purchases(Variable):
    label = "Stamp Duty on non-residential property"
    documentation = (
        "Tax charge from purchase or rental of non-residential property"
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class stamp_duty(Variable):
    label = "Stamp Duty Land Tax"
    documentation = "Total tax liability for Stamp Duty Land Tax"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
