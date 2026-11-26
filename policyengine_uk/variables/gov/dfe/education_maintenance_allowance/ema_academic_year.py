from policyengine_uk.model_api import *


class ema_academic_year(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = STOCK
    label = "EMA assessment academic year"
    documentation = (
        "The academic assessment year is independent of the requested model cash "
        "year. Only the source-supported 2026/27 assessment is in scope; a different "
        "fiscal year must not silently select another assessment. This is a supplied "
        "assessment or allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
