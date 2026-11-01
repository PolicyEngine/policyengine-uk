from policyengine_uk.model_api import *


class sdlt_on_non_residential_property_transactions(Variable):
    label = "Stamp Duty on non-residential property"
    documentation = (
        "Tax charge from purchase of non-residential property. When "
        "gov.hmrc.stamp_duty.non_residential.purchase_charged_on_whole_price "
        "is true, the formula charges the rate of the band the price falls in "
        "on the whole price, where a price falls in the highest band whose "
        "threshold it exceeds. Otherwise it charges each band's rate on the "
        "slice of the price in that band."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/55"

    def formula(household, period, parameters):
        non_residential = parameters(period).gov.hmrc.stamp_duty.non_residential
        price = household("non_residential_property_purchased", period)
        scale = non_residential.purchase
        thresholds = np.array(scale.thresholds, dtype=float)
        rates = np.array(scale.rates, dtype=float)
        # Each band covers prices that exceed its threshold and do not exceed
        # the next one; a price of zero falls in the first band.
        exceeds = np.asarray(price, dtype=float)[:, None] > thresholds[None, :]
        band = max_(exceeds.sum(axis=1) - 1, 0)
        whole_price_tax = rates[band] * price
        slice_tax = scale.calc(price)
        return where(
            non_residential.purchase_charged_on_whole_price,
            whole_price_tax,
            slice_tax,
        )
