from policyengine_uk.model_api import *


class ema_incompatible_course_funding(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    default_value = False
    label = "EMA incompatible course funding"
    documentation = (
        "Record the selected scheme prohibition on paid course or placement, training "
        "allowance or overlapping public support. This does not replace the remaining "
        "course conditions. This is a supplied assessment or allocation fact, not "
        "whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
