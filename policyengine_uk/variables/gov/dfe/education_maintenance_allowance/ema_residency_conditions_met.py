from policyengine_uk.model_api import *


class ema_residency_conditions_met(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "EMA residency conditions met"
    documentation = (
        "This supplied determination covers the selected scheme nationality, "
        "residence timing, temporary-absence and transitional categories. Current "
        "household country or nationality alone does not establish it. This is a "
        "supplied assessment or allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
