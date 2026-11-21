from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_flat_rate_turnover(Variable):
    label = "VAT flat rate turnover"
    documentation = (
        "All of the firm's supplies including VAT: standard- and "
        "reduced-rated supplies grossed up by their rates, plus zero-rated "
        "and exempt supplies."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.gov.uk/guidance/flat-rate-scheme-for-small-businesses-vat-notice-733--2"
    adds = [
        "firm_standard_rated_supplies",
        "firm_reduced_rated_supplies",
        "firm_zero_rated_supplies",
        "firm_exempt_supplies",
        "firm_output_vat",
    ]
