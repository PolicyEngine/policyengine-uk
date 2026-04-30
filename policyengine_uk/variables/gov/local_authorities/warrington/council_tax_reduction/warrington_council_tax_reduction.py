from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    legacy_council_tax_reduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_warrington_working_age,
)
from policyengine_uk.variables.input.council_tax_band import CouncilTaxBand


class warrington_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Warrington Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.warrington.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        council_tax_band = benunit.household("council_tax_band", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        income_below_applicable_amount = benunit(
            "council_tax_reduction_income_below_applicable_amount",
            period,
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit",
            period,
        )
        working_age = is_warrington_working_age(
            local_authority, country, has_pensioner
        )
        class_d = working_age & (
            income_below_applicable_amount | relevant_income_based_benefit
        )
        band_a = council_tax_band == CouncilTaxBand.A
        maximum_support_rate = select(
            [
                class_d & band_a,
                class_d,
            ],
            [
                ctr.maximum_support_rate.class_d.band_a,
                ctr.maximum_support_rate.class_d.other_bands,
            ],
            default=ctr.maximum_support_rate.class_e,
        )
        return legacy_council_tax_reduction(
            benunit,
            period,
            ctr,
            working_age,
            "warrington_council_tax_reduction_non_dep_deductions",
            maximum_support_rate=maximum_support_rate,
            maximum_eligible_liability_variable=(
                "warrington_council_tax_reduction_maximum_eligible_liability"
            ),
        )
