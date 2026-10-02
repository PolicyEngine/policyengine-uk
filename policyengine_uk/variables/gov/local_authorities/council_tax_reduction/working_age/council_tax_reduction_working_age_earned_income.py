from policyengine_uk.model_api import *


class council_tax_reduction_working_age_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction net earned income"
    documentation = (
        "Annual net earnings of the claimant and partner for a working-age "
        "council tax reduction claim in Scotland or Wales, before earnings "
        "disregards. Income tax and National Insurance are deducted from each "
        "person's earnings up to those earnings; in Wales any tax the earnings "
        "cannot absorb is disregarded from unearned income instead (see "
        "council_tax_reduction_working_age_unabsorbed_tax)."
    )
    definition_period = YEAR
    unit = GBP
    adds = ["council_tax_reduction_working_age_person_earned_income"]
