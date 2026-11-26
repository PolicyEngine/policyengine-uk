from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class ema_assessment_country(Variable):
    value_type = Enum
    entity = Person
    definition_period = YEAR
    possible_values = Country
    default_value = Country.UNKNOWN
    label = "EMA assessment country"
    documentation = (
        "Funding scheme being assessed; no inference from legacy EMA or provider "
        "country. This is a supplied assessment or allocation fact, not "
        "whole-programme eligibility."
    )
    reference = (
        "https://www.gov.wales/sites/default/files/publications/2026-04/the-education-maintenance-allowance-wales-scheme-2026-2027.pdf",
        "https://www.highland.gov.uk/downloads/file/962/ema-guidance-notes-2025-26",
        "https://www.nidirect.gov.uk/sites/default/files/2026-06/ema-ni-application-notes-2627-e-o-PDF_0.pdf",
        "https://www.nidirect.gov.uk/articles/education-maintenance-allowance-explained",
    )
