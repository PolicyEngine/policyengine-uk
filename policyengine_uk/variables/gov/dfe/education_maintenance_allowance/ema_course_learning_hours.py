from policyengine_uk.model_api import *


class ema_course_learning_hours(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = STOCK
    label = "EMA course learning hours"
    documentation = (
        "Count the source-defined scheduled guided or learning-session hours. It is "
        "an assessment stock, not an annual hours total to divide over periods. This "
        "is a supplied assessment or allocation fact, not whole-programme "
        "eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
