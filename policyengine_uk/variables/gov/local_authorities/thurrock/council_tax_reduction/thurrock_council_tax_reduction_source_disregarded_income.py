from policyengine_uk.model_api import *


class thurrock_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Thurrock CTR source-disregarded annual income"
    documentation = "Use this input for source-listed Schedule 3 or Schedule 4 income disregards not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    unit = GBP
    reference = "https://thurrock.moderngov.co.uk/documents/s51034/Enc.%201%20for%20Local%20Council%20Tax%20Support%20Scheme%202026-27.pdf"
    default_value = 0
