from policyengine_uk.model_api import *


class south_gloucestershire_council_tax_reduction_self_employment_floor_applies(
    Variable
):
    value_type = bool
    entity = Person
    label = "South Gloucestershire CTR self-employed nil-income floor applies"
    definition_period = YEAR
    reference = "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf"
    documentation = (
        "Whether the applicant or partner is a self-employed earner after the "
        "initial one-year trading period whose self-employed income is nil, so "
        "the source-listed nil-income floor applies."
    )
