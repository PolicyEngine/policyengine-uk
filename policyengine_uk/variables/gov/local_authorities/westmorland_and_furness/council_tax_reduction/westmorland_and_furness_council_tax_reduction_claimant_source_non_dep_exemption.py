from policyengine_uk.model_api import *


class westmorland_and_furness_council_tax_reduction_claimant_source_non_dep_exemption(
    Variable
):
    value_type = bool
    entity = Person
    label = "Whether a Westmorland and Furness CTR claimant has a section 30.6 non-dependant deduction exemption not otherwise modeled"
    documentation = "Covers source-listed claimant exemptions not otherwise represented in PolicyEngine UK, such as suspended entitlement to disability benefits."
    definition_period = YEAR
    reference = "https://www.westmorlandandfurness.gov.uk/sites/default/files/2026-03/Westmorland%20%26%20Furness%20Council%20%20CTR%20Scheme%20202627%20%28accessible%20March%202026%29.pdf"
    default_value = False
