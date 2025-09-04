from policyengine_uk.model_api import *

label = "Business Group"
description = "Business group variables."


class business_group_id(Variable):
    value_type = int
    entity = BusinessGroup
    label = "business group ID"
    documentation = "Unique identifier for each business group"
    definition_period = YEAR
    quantity_type = STOCK
