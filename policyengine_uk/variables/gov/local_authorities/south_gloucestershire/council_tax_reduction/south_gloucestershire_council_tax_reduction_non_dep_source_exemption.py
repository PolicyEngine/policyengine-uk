from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "South Gloucestershire CTR source-listed non-dependant exclusion"
    definition_period = YEAR
    reference = "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf"
    documentation = (
        "Whether a person is excluded from South Gloucestershire's non-dependant "
        "definition for source-listed reasons not otherwise modeled, such as "
        "certain joint-liability, commercial-occupier, or voluntary live-in carer "
        "cases."
    )
