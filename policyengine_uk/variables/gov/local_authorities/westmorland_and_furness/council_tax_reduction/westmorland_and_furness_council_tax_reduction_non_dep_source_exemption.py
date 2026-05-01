from policyengine_uk.model_api import *


class westmorland_and_furness_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Westmorland and Furness CTR non-dependant has a section 30.7 or 30.8 deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, long-term patient status, armed forces away, or Schedule 1 discount-disregarded cases."
    definition_period = YEAR
    reference = "https://www.westmorlandandfurness.gov.uk/sites/default/files/2026-03/Westmorland%20%26%20Furness%20Council%20%20CTR%20Scheme%20202627%20%28accessible%20March%202026%29.pdf"
    default_value = False
