from policyengine_core.variables import Variable
from policyengine_uk.entities import Firm


class firm_weight(Variable):
    value_type = float
    entity = Firm
    label = "Firm weight"
    definition_period = "year"
    documentation = "Weight for firm-level calculations"

    def formula(firm, period, parameters):
        # Default weight of 1 for each firm
        # This would typically be based on survey weights in real data
        return firm("firm_count", period)
