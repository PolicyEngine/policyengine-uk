from policyengine_uk.model_api import *


class ema_prior_supported_academic_years(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = -1
    quantity_type = STOCK
    label = "EMA prior supported academic years"
    documentation = (
        "Count source-defined prior supported academic years. Minus one means "
        "unknown; zero means verified none. Do not infer this history from current "
        "age. This is a supplied assessment or allocation fact, not whole-programme "
        "eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
