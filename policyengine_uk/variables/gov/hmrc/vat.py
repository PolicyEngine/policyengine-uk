from policyengine_uk.model_api import *
from policyengine_uk.utils.vat import vat_grossing_factor


class vat(Variable):
    label = "VAT excluding private school fees"
    documentation = (
        "Receipt-calibrated VAT less private school fees' share of VAT "
        "receipts, which private_school_vat counts separately."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        full_rate_consumption = household("full_rate_vat_consumption", period)
        reduced_rate_consumption = household("reduced_rate_vat_consumption", period)
        p = parameters(period).gov
        raw_vat = (
            full_rate_consumption * p.hmrc.vat.standard_rate
            + reduced_rate_consumption * p.hmrc.vat.reduced_rate
        )
        # Survey consumption under-records spending, and households bear only
        # part of VAT liabilities, so household VAT is grossed up to receipts.
        gross_vat = raw_vat / vat_grossing_factor(p.simulation)
        # Those receipts include VAT on private school fees, which
        # private_school_vat counts. Every household's VAT gives up the fees'
        # share of receipts, so the allocation never makes it negative and
        # school-specific reforms change only private_school_vat.
        return gross_vat * (1 - p.simulation.vat.private_school_share_of_receipts)
