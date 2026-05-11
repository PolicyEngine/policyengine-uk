from policyengine_uk.model_api import *


class tendring_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Tendring Council Tax Reduction non-dependant deductions"
    documentation = "Tendring paragraph 58.0 is marked 'Not Used', so the working-age local scheme does not make non-dependant deductions."
    definition_period = YEAR
    unit = GBP
    reference = "https://legacy.tendringdc.gov.uk/sites/default/files/documents/Council_Tax/Tendring%20S13A%20202627%20Scheme%20Final.pdf"

    def formula(benunit, period, parameters):
        return 0
