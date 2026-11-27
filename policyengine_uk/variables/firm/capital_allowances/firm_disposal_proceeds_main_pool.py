from policyengine_uk.model_api import *


class firm_disposal_proceeds_main_pool(Variable):
    value_type = float
    entity = Firm
    label = "Firm main pool disposal proceeds"
    documentation = "Disposal values brought into account in the main pool for plant and machinery sold or scrapped in the year, capped at original cost. Includes the proceeds of fully expensed plant, which firm_disposal_proceeds_full_expensing also reports."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
