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
        coverage = vat_grossing_factor(p.simulation)
        # Match vat's receipt allocation under baseline policy. Using this
        # simulation's attendance and fee assumptions makes assumptions-only
        # reforms leave both VAT change measures at zero.
        return raw_vat / coverage - household("baseline_private_school_vat", period)
