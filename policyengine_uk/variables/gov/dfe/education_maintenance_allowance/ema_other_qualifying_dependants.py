from policyengine_uk.model_api import *


class ema_other_qualifying_dependants(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    default_value = 0
    quantity_type = STOCK
    label = "Other qualifying dependants in the EMA assessment"
    documentation = (
        "Exclude the applicant and use the selected scheme definition of other people "
        "sharing the assessment income. Do not substitute generic household size or "
        "children under 16. The assessment facts must establish the count. This is a "
        "supplied assessment or allocation fact, not whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
