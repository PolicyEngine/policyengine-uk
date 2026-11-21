from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat_taxable_turnover(Variable):
    label = "VAT taxable turnover"
    documentation = (
        "Value of the firm's taxable supplies in the year, excluding VAT: "
        "standard-, reduced- and zero-rated supplies. Exempt supplies are not "
        "taxable supplies."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1994/23/section/4"
    adds = [
        "firm_standard_rated_supplies",
        "firm_reduced_rated_supplies",
        "firm_zero_rated_supplies",
    ]
