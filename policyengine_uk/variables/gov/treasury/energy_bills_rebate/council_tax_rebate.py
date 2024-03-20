from policyengine_uk.model_api import *
from policyengine_uk.variables.input.housing import (
    CouncilTaxBand,
)


class ebr_council_tax_rebate(Variable):
    label = "Council Tax Rebate (EBR)"
    documentation = "Council Tax discount under the Energy Bills Rebate."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        ctr = parameters(
            period
        ).gov.treasury.energy_bills_rebate.council_tax_rebate
        ct_band = household("council_tax_band", period)
        eligible = np.any(
            np.array(
                [
                    ct_band == getattr(CouncilTaxBand, band)
                    for band in ctr.bands
                ]
            ),
            axis=0,
        )
        return eligible * ctr.amount
