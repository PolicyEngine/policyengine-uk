from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    english_council_tax_band_ratio,
    is_warrington_working_age,
)


class warrington_council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Warrington maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        england_council_tax = parameters(
            period
        ).gov.local_authorities.england.council_tax
        ctr = parameters(period).gov.local_authorities.warrington.council_tax_reduction
        council_tax = household("council_tax", period)
        band_ratio = english_council_tax_band_ratio(
            household("council_tax_band", period),
            england_council_tax.band_ratio,
        )
        cap_band_ratio = ctr.maximum_liability.cap_band_ratio
        capped_liability = council_tax * cap_band_ratio / band_ratio
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        claimant_income_below_applicable_amount = household.any(
            claimant_benunit
            & person.benunit(
                "council_tax_reduction_income_below_applicable_amount",
                period,
            )
        )
        claimant_relevant_income_based_benefit = household.any(
            claimant_benunit
            & person.benunit(
                "council_tax_reduction_relevant_income_based_benefit",
                period,
            )
        )
        working_age = is_warrington_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        capped = (
            working_age
            & ~claimant_income_below_applicable_amount
            & ~claimant_relevant_income_based_benefit
            & (band_ratio > cap_band_ratio)
        )
        return where(capped, capped_liability, council_tax)
