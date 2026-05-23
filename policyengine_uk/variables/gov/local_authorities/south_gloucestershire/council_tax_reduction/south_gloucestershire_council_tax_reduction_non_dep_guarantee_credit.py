from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction_non_dep_guarantee_credit(Variable):
    value_type = bool
    entity = Person
    label = "Whether this South Gloucestershire non-dependant receives Pension Credit Guarantee Credit"
    definition_period = YEAR
    reference = "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf"
    documentation = (
        "Source input for the South Gloucestershire non-dependant low-rate "
        "passported-benefit rule that applies to Pension Credit Guarantee "
        "Credit, not Savings Credit alone."
    )
