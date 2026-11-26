from policyengine_uk.model_api import *


class ema_academic_year_start_date(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = STOCK
    unit = "date"
    label = "EMA institution academic-year start date"
    documentation = (
        "Zero selects the source-defined ordinary anchor for the selected scheme. A "
        "nonzero value records a genuine earlier institution start only where the "
        "scheme supports it; it is not an arbitrary fiscal-date override. This is a "
        "supplied assessment or allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
