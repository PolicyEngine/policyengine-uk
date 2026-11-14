from policyengine_uk.model_api import *


class sdlt_on_non_residential_property_transactions(Variable):
    label = "Stamp Duty on non-residential property"
    documentation = (
        "Tax charge from purchase of non-residential property. When "
        "gov.hmrc.stamp_duty.non_residential.purchase_charged_on_whole_price "
        "holds true, HMRC charges the whole price at the rate for the band "
        "the price falls in: the highest band whose threshold the price "
        "exceeds, or no band, and so no tax, when the price exceeds no "
        "threshold. When it holds false, HMRC charges each band's rate on the "
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
        # the next one. A price that exceeds no threshold falls in no band.
        exceeds = np.asarray(price, dtype=float)[:, None] > thresholds[None, :]
        band = exceeds.sum(axis=1) - 1
        whole_price_rate = where(band >= 0, rates[max_(band, 0)], 0)
        whole_price_tax = whole_price_rate * price
        slice_tax = scale.calc(price)
        return where(
            non_residential.purchase_charged_on_whole_price,
            whole_price_tax,
            slice_tax,
        )
