from policyengine_uk.model_api import *


class firm_structures_and_buildings_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Firm structures and buildings allowance"
    documentation = (
        "Straight-line structures and buildings allowance on the qualifying "
        "cost of non-residential structures in qualifying use, a full year's "
        "allowance on this year's and earlier years' cost. The enhanced rate "
        "on special tax sites is not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/270AA"

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.structures_and_buildings_allowance.rate
        cost = add(
            firm,
            period,
            ["firm_capex_structures", "firm_sba_qualifying_cost_brought_forward"],
        )
        return rate * cost
