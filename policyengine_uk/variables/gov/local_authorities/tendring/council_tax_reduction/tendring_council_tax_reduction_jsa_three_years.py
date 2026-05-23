from policyengine_uk.model_api import *


class tendring_council_tax_reduction_jsa_three_years(Variable):
    value_type = bool
    entity = BenUnit
    label = "Tendring CTR source input - applicant or partner has received Jobseeker's Allowance for three years or more"
    documentation = "Tendring paragraph 57.1A reduces maximum Council Tax Reduction from 80 percent to 60 percent where the applicant or partner has been in receipt of Jobseeker's Allowance for a period of three years or more. PolicyEngine UK does not model the duration of JSA receipt, so this Tendring-scoped source input lets the case assert that condition. Default False."
    definition_period = YEAR
    reference = "https://legacy.tendringdc.gov.uk/sites/default/files/documents/Council_Tax/Tendring%20S13A%20202627%20Scheme%20Final.pdf"
    default_value = False
