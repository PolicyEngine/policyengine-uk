from policyengine_uk.model_api import *


class basildon_council_tax_reduction_source_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Basildon CTR source-defined protected group"
    documentation = "Covers source-listed protected-group triggers not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.basildon.gov.uk/media/11563/Basildon-Council-Council-Tax-Reduction-Scheme-2026-27/pdf/Basildon_S13A_202627_Final.pdf?m=1771316212763"
    default_value = False
