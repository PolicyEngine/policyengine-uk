from policyengine_uk.model_api import *


class EMAFinancialCategory(Enum):
    UNKNOWN = "Unknown"
    DEPENDENT = "Dependent applicant"
    INDEPENDENT = "Independent applicant"
    IN_LOCAL_AUTHORITY_CARE = "In local authority care"
    WALES_CARE_LEAVER = "Wales statutory care leaver"
    RESPONSIBLE_FOR_OWN_CHILD = "Responsible for their own child"
    INCOME_SUPPORT = "Income Support"
    INCOME_RELATED_ESA = "Income-related Employment and Support Allowance"
    CONTRIBUTION_BASED_ESA = "Contribution-based Employment and Support Allowance"
    UNIVERSAL_CREDIT = "Universal Credit"
    YOUTH_JUSTICE = "Specified Wales youth-justice custody or detention"


class ema_financial_category(Variable):
    value_type = Enum
    entity = Person
    definition_period = YEAR
    possible_values = EMAFinancialCategory
    default_value = EMAFinancialCategory.UNKNOWN
    label = "EMA financial assessment category"
    documentation = (
        "This records the verified assessment category and supporting historical "
        "facts, not whole-programme eligibility. Wales statutory care-leaver status "
        "requires its specific care history. Scottish exemption for care means "
        "current local-authority care, not every care leaver. NI independence "
        "categories do not automatically exempt assessed income. Income-related and "
        "contribution-based ESA are distinct. This is a supplied assessment or "
        "allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
