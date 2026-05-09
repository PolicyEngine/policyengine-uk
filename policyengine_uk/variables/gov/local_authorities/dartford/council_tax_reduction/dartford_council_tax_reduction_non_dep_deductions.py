from policyengine_uk.model_api import *


class dartford_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Dartford Council Tax Reduction non-dependant deductions"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.dartford.gov.uk/downloads/file/2814/local-council-tax-reduction-scheme-dbc-2026-2027"

    def formula(benunit, period, parameters):
        return 0
