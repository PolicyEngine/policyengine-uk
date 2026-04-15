from policyengine_uk.model_api import *


class travel_grant_receives_means_tested_nhs_bursary(Variable):
    value_type = bool
    entity = Person
    label = "Receives a means-tested NHS bursary for Travel Grant purposes"
    documentation = "Whether the student receives a means-tested NHS bursary or award, which blocks Travel Grant for UK clinical placements."
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period
