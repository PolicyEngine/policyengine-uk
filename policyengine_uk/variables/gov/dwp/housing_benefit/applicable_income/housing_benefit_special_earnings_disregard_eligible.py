from policyengine_uk.model_api import *


class housing_benefit_special_earnings_disregard_eligible(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    default_value = False
    label = "Qualifies for the full Housing Benefit special earnings disregard"
    documentation = (
        "Whether the full special standard amount may legally be deducted "
        "from the benefit unit's combined earnings, subject to the earnings "
        "cap. Derived for working-age disability/severe-premium routes and "
        "pension-age qualifying benefit receipt, blindness or carer premium. "
        "Other full-amount routes may be pre-assessed as an input, including "
        "the applicable job/partner earnings allocation: mere occupation or "
        "carer status is not sufficient. Partial carer/occupation allocations "
        "below the full amount are not reconstructed by this Boolean. Existing "
        "premium/benefit qualification approximations are inherited. No "
        "dataset mapping for residual pre-assessment is verified; a false "
        "fallback may omit qualifying ESA phase/history/occupation routes."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5",
    )

    def formula(benunit, period, parameters):
        working = (benunit("disability_premium", period) > 0) | (
            benunit("severe_disability_premium", period) > 0
        )
        person = benunit.members
        qualifying_receipt = (
            add(
                person,
                period,
                [
                    "attendance_allowance",
                    "dla_sc",
                    "dla_m",
                    "pip_dl",
                    "pip_m",
                    "armed_forces_independence_payment",
                ],
            )
            > 0
        )
        pension = benunit.any(
            person("is_claimant_or_partner", period)
            & (qualifying_receipt | person("is_blind", period))
        ) | (benunit("carer_premium", period) > 0)
        # Working-age carer/occupation routes restrict which person's/job's
        # earnings may be disregarded. Do not automatically apply £20 to an
        # ordinary earner solely because their non-earning partner cares.
        return where(
            benunit("housing_benefit_pension_age_regulations_apply", period),
            pension,
            working,
        )
