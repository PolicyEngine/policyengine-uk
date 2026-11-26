from policyengine_uk.model_api import *


class ema_qualifying_bonus_count(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = FLOW
    label = "EMA qualifying bonus count"
    documentation = (
        "Actual institution-qualified Northern Ireland bonuses allocated to this "
        "exact cash year, including required objectives, signatures and timing. "
        "January or June alone does not establish a bonus, and the caller must not "
        "allocate the same earned bonus twice. This is a supplied assessment or "
        "allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
