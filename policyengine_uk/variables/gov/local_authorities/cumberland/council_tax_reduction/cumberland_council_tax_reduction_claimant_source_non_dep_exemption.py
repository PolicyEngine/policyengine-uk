from policyengine_uk.model_api import *


class cumberland_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Cumberland Council Tax Reduction claimant has a source-listed non-dependant deduction exemption"
    definition_period = YEAR
    reference = "https://www.cumberland.gov.uk/sites/default/files/2026-04/cumberland_council_final_council_tax_reduction_ctr_scheme_for_2026_to_2027.pdf"
