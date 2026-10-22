from policyengine_uk.model_api import *


class council_tax_reduction_severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age CTR severe disability premium"
    documentation = (
        "The shared legacy premium's amount before its non-dependant test, "
        "with the Council Tax Reduction-specific family test applied. This "
        "allows either direction of a difference between the Universal Credit "
        "and Child Benefit young-person definitions. The test retains the "
        "existing classification for looked-after residents and other benefit "
        "units; see has_non_dependant_for_council_tax_reduction_severe_disability_premium. "
        "Pension-age Council Tax Reduction continues to use its separate premium."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/8",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/13",
    )

    def formula(benunit, period, parameters):
        amount = benunit("severe_disability_premium_before_non_dependant_test", period)
        no_non_dependant = ~benunit(
            "has_non_dependant_for_council_tax_reduction_severe_disability_premium",
            period,
        )
        return amount * no_non_dependant
