from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
    is_bury_working_age,
)


class bury_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Bury maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        england_council_tax = parameters(
            period
        ).gov.local_authorities.england.council_tax
        ctr = parameters(period).gov.local_authorities.bury.council_tax_reduction
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            england_council_tax.band_ratio,
        )
        cap_band_ratio = ctr.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        working_age = is_bury_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        protected = (
            household.max(
                household.members.benunit(
                    "bury_council_tax_reduction_protected_group", period
                )
            )
            > 0
        )
        capped = working_age & ~protected & (band_ratio > cap_band_ratio)
        return where(capped, capped_liability, council_tax)
