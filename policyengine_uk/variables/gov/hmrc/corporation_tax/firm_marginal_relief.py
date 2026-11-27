import numpy as np

from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_marginal_relief(Variable):
    value_type = float
    entity = Firm
    label = "Firm corporation tax marginal relief"
    documentation = (
        "Marginal relief for companies with augmented profits above the lower "
        "limit and not above the upper limit: the standard fraction times the "
        "upper limit less augmented profits, times taxable total profits over "
        "augmented profits. None for a close investment-holding company or a "
        "non-UK-resident company (firm_small_profits_rate_excluded)."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/18B",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/18N",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax
        if not p.small_profits_rate_applies:
            return 0
        augmented = firm("firm_augmented_profits", period)
        taxable = firm("firm_taxable_profit", period)
        lower = firm("firm_corporation_tax_lower_limit", period)
        upper = firm("firm_corporation_tax_upper_limit", period)
        excluded = firm("firm_small_profits_rate_excluded", period)
        in_band = (augmented > lower) & (augmented <= upper) & ~excluded
        profit_ratio = np.divide(
            taxable,
            augmented,
            out=np.zeros_like(taxable),
            where=augmented > 0,
        )
        relief = p.marginal_relief.fraction * (upper - augmented) * profit_ratio
        return where(in_band, relief, 0)
