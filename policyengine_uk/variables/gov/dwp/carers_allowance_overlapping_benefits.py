from policyengine_uk.model_api import *


class carers_allowance_overlapping_benefits(Variable):
    value_type = float
    entity = Person
    label = "Personal benefits that overlap with Carer's Allowance"
    documentation = (
        "Other personal benefits by which regulation 12 of the Social Security "
        "(Overlapping Benefits) Regulations 1979 reduces Carer's Allowance."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/4",
        "https://www.legislation.gov.uk/uksi/1979/597/regulation/12",
    )
    adds = "gov.dwp.carers_allowance.overlapping_benefits"
