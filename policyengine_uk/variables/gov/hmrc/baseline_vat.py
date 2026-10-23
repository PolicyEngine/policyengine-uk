from policyengine_uk.model_api import *
from policyengine_uk.utils.vat import vat_grossing_factor


class baseline_vat(Variable):
    label = "baseline VAT excluding private school fees"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        full_rate_consumption = household("full_rate_vat_consumption", period)
        reduced_rate_consumption = household("reduced_rate_vat_consumption", period)
        p = parameters(period).baseline.gov
        raw_vat = (
            full_rate_consumption * p.hmrc.vat.standard_rate
            + reduced_rate_consumption * p.hmrc.vat.reduced_rate
        )
        # Survey consumption under-records spending, and households bear only
        # part of VAT liabilities, so household VAT is grossed up to receipts.
        gross_vat = raw_vat / vat_grossing_factor(p.simulation)
        # vat's allocation of private school fees' share of receipts. The
        # share is read from this simulation's parameters, as
        # baseline_private_school_vat reads its assumptions: the baseline tree
        # reads 1 January, before each fiscal year's value takes effect.
        share = parameters(period).gov.simulation.vat.private_school_share_of_receipts
        return gross_vat * (1 - share)
