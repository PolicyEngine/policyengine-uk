from policyengine_uk.model_api import *


class is_in_first_year_of_apprenticeship(Variable):
    value_type = bool
    entity = Person
    label = "In the first 12 months of the current apprenticeship"
    documentation = (
        "Whether this person is within the first 12 months of the current "
        "apprenticeship employment, including employment with a previous "
        "employer where statutory continuity is preserved. This is an annual "
        "caller-supplied classification, not an academic year or an inferred "
        "start date. It does not by itself establish apprentice status."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2015/621/regulation/5",
        "https://www.gov.uk/hmrc-internal-manuals/national-minimum-wage-manual/nmwm05300",
    )
