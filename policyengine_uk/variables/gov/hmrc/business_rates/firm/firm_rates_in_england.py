from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_rates_in_england(Variable):
    value_type = bool
    entity = Firm
    label = "Firm pays English business rates"
    documentation = (
        "Whether the firm's business rates follow the English rules: "
        "firm_in_england is true and firm_region is not Wales, Scotland or "
        "Northern Ireland. The English reliefs apply only where this is true; "
        "Wales and Scotland have their own reliefs in "
        "firm_business_rates_reliefs."
    )
    definition_period = YEAR

    def formula(firm, period, parameters):
        region = firm("firm_region", period)
        regions = region.possible_values
        return (
            firm("firm_in_england", period)
            & (region != regions.WALES)
            & (region != regions.SCOTLAND)
            & (region != regions.NORTHERN_IRELAND)
        )
