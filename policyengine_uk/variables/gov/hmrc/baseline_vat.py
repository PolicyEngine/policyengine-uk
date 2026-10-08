from policyengine_uk.model_api import *


class baseline_vat(Variable):
    label = "baseline VAT"
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
        coverage = (
            p.simulation.vat.survey_consumption_coverage
            * p.simulation.vat.household_share_of_receipts
        )
        return raw_vat / coverage
