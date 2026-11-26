from policyengine_uk.model_api import *


class ema_assessed_income(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = STOCK
    unit = GBP
    label = "EMA assessed annual income"
    documentation = (
        "Supply the correctly defined assessment-group total, including an accepted "
        "reassessment where applicable. The normal source bases are 2024/25 for Wales "
        "and Northern Ireland and 2025/26 for the scoped Highland scheme. Do not "
        "substitute current household disposable income or deduct pension and "
        "expenses twice. This is an assessment stock, not annual cash flow. This is a "
        "supplied assessment or allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
