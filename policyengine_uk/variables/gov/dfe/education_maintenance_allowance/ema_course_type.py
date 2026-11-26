from policyengine_uk.model_api import *


class EMACourseType(Enum):
    UNKNOWN = "Unknown"
    SCHOOL = "School"
    FURTHER_EDUCATION = "Further education"
    PREPARATION_FOR_LIFE_OR_WORK = "Preparation for life or work"


class ema_course_type(Variable):
    value_type = Enum
    entity = Person
    definition_period = YEAR
    possible_values = EMACourseType
    default_value = EMACourseType.UNKNOWN
    label = "EMA course type"
    documentation = (
        "This is the actual course type at the assessment, not an education stage "
        "imputed from age. Only source-supported school, further-education or "
        "approved preparation routes can qualify. This is a supplied assessment or "
        "allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
