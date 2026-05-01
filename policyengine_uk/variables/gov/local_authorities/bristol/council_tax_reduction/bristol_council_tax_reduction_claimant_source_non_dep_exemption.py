from policyengine_uk.model_api import *


class bristol_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Bristol Council Tax Reduction claimant has a source-listed non-dependant deduction exemption"
    definition_period = YEAR
    reference = "https://www.bristol.gov.uk/files/documents/10754-bristol-council-tax-reduction-scheme-2026/file"
