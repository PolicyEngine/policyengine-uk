from policyengine_uk.model_api import *


class ema_prior_positive_or_negative_confirmations(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = -1
    quantity_type = STOCK
    label = "EMA prior positive or negative confirmations"
    documentation = (
        "Northern Ireland positive and negative weekly confirmations before the "
        "allocated block, under the lifetime limit. Actual current payable weeks must "
        "already exclude current negative confirmations and positives after "
        "exhaustion; a total cannot reconstruct their order. Minus one is unknown. "
        "This is a supplied assessment or allocation fact, not whole-programme "
        "eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
