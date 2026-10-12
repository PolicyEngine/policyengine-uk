from policyengine_uk.model_api import *


class property_finance_costs_brought_forward(Variable):
    value_type = float
    entity = Person
    label = "residential property finance costs brought forward"
    documentation = (
        "Finance costs of earlier years that have not yet been relieved and "
        "are carried forward into this year (the brought-forward amount of "
        "ITTOIA 2005 s. 274AA(4)). They are relieved with this year's "
        "property_finance_costs. The previous year's "
        "property_finance_costs_carried_forward."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, s. 274AA(4)",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/274AA",
    )
    quantity_type = FLOW
    # Projected with the costs they came from.
    uprating = "gov.economic_assumptions.indices.obr.mortgage_interest"
