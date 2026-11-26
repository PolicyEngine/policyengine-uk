from policyengine_uk.model_api import *


class EMAExtendedDurationCategory(Enum):
    NONE = "No extended-duration category"
    VULNERABLE = "Source-defined vulnerable student"
    YOUNG_CARER = "Source-defined young carer"


class ema_extended_duration_category(Variable):
    value_type = Enum
    entity = Person
    definition_period = YEAR
    possible_values = EMAExtendedDurationCategory
    default_value = EMAExtendedDurationCategory.NONE
    label = "EMA extended duration category"
    documentation = (
        "Scotland vulnerable/young-carer extended duration category; source "
        "definitions required. This is a supplied assessment or allocation fact, not "
        "whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
