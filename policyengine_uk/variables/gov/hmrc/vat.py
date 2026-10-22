from policyengine_uk.model_api import *
from policyengine_uk.utils.vat import vat_grossing_factor


class vat(Variable):
    label = "VAT excluding private school fees"
    documentation = (
        "Receipt-calibrated VAT less the baseline school-fee tax base at the "
        "current standard rate. Private school VAT is counted separately. "
        "The residual can be negative when recorded consumption is too low "
        "to cover the school-fee allocation."
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
        coverage = vat_grossing_factor(p.simulation)
        # The receipts used to fit coverage already include school-fee VAT.
        # Reclassify its baseline tax base, at the current standard rate, so
        # neither current law nor a standard-rate reform counts it twice.
        # School-specific rate/exemption reforms change the separate head.
        baseline_school_vat = household("baseline_private_school_vat", period)
        baseline_standard_rate = parameters(period).baseline.gov.hmrc.vat.standard_rate
        # Form the scalar ratio first: it is exactly one at baseline. A
        # float32 multiply then divide can otherwise create a tiny vat_change.
        school_vat_in_receipts = baseline_school_vat * (
            p.hmrc.vat.standard_rate / baseline_standard_rate
        )
        return raw_vat / coverage - school_vat_in_receipts
