from policyengine_uk.model_api import *


class council_tax_reduction_working_age_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction net earned income"
    documentation = (
        "Annual net earnings of the claimant and partner for a working-age "
        "council tax reduction claim in Scotland or Wales, before earnings "
        "disregards: the sum of each person's net earnings (see "
        "council_tax_reduction_working_age_person_earned_income)."
    )
    definition_period = YEAR
    unit = GBP
    adds = ["council_tax_reduction_working_age_person_earned_income"]
