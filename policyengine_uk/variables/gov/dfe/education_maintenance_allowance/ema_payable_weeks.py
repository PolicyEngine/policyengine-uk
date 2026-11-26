from policyengine_uk.model_api import *


class ema_payable_weeks(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = FLOW
    label = "EMA payable weeks"
    documentation = (
        "Actual lawfully payable weeks of this one academic assessment, allocated by "
        "the caller to this exact requested model year. They must already respect "
        "agreement, progress, authorised absence, holidays, application or backdating "
        "and any reassessment timing. No automatic 52-week award or chronological "
        "ledger is inferred; an earlier-year input is not a new allocation. This is a "
        "supplied assessment or allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
