from policyengine_core.variables import Variable
from policyengine_uk.entities import Firm
import numpy as np


class firm_count(Variable):
    value_type = float
    entity = Firm
    label = "Number of firms"
    definition_period = "year"
    documentation = (
        "Count of firms represented (typically 1 for individual firm records)"
    )

    def formula(firm, period, parameters):
        # Each firm record represents one firm by default
        return np.ones(firm.count)
