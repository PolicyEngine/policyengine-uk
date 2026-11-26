from policyengine_uk.model_api import *


class ema_institution_recommends_twentieth_year(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "EMA institution recommends twentieth year"
    documentation = (
        "True records the institution advice required by the Wales twentieth-birthday "
        "route; it does not qualify every 20-year-old. This is a supplied assessment "
        "or allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
