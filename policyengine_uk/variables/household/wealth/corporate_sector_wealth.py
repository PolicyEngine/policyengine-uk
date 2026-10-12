from policyengine_uk.model_api import *


class corporate_sector_wealth(Variable):
    label = "wealth exposed to the corporate sector"
    documentation = (
        "Corporate wealth held directly or through investment funds plus private "
        "pension wealth, which pension funds invest in the corporate sector. The "
        "allocation key for corporate tax incidence (shareholding), corporate "
        "land value and the employer NI capital response. A compatibility "
        "allocation proxy: it preserves the pre-split key (pension funds hold "
        "corporate assets) rather than independently validating how much "
        "capitalised pension wealth is corporate-sector exposure. Equals "
        "corporate_wealth on datasets built before private pension wealth was "
        "split out of it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    adds = [
        "corporate_wealth",
        "private_pension_wealth",
    ]
