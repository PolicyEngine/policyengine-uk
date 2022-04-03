from openfisca_uk.model_api import *
from openfisca_uk.variables.household.consumption.expense import CouncilTaxBand


class ebr_council_tax_rebate(Variable):
    label = "Council Tax Rebate (EBR)"
    documentation = "Council Tax discount under the Energy Bills Rebate."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        ctr = parameters(
            period
        ).treasury.energy_bills_rebate.council_tax_rebate
        ct_amount = household("council_tax", period)
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
