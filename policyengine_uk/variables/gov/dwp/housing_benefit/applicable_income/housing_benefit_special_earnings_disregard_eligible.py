from policyengine_uk.model_api import *


class housing_benefit_special_earnings_disregard_eligible(Variable):
    """Implement the working-age premium route and the modelled pension-age
    paragraph 5 qualifying routes.

    GB SI 2006/214 Sch. 4 and NI SR 2006/406 Sch. 5 para. 5(1)(a)
    list the following receipts implemented here:
    (ii) "severe disablement allowance under section 68 of the Act";
    (iii) "attendance allowance";
    (iv) "disability living allowance under sections 71 to 76 of the Act";
    (vi) "the disability element or the severe disability element of working
    tax credit"; and (viii) "personal independence payment".
    GB (ix) and NI (iva) list "armed forces independence payment".
    Para. 5(1)(b) adds those "certified as severely sight impaired or blind
    by a consultant ophthalmologist", represented here by is_blind.

    Only claimant/partner receipts qualify. Working Tax Credit and its
    disability elements are benefit-unit variables whose formulas scope
    entitlement to the claimant/partner; a positive element alone does not
    establish receipt of the award.

    Not derived: long-term Incapacity Benefit (5(1)(a)(i)), prescribed war
    pension/personal injury mobility supplements (v), main-phase ESA (vii),
    continuous incapacity for 196 days if terminally ill or 364 days otherwise
    (5(1)(c)), assessed LCW/LCWRA or the specified assessment-phase exceptions
    (5(1)(d)), and protected earlier HB awards with eight-week continuity
    (5(2)-(3)). Pension age disability payment, Scottish adult disability
    living allowance and adult disability payment also lack dedicated
    variables here; their upstream mapping to AA/DLA/PIP is not verified.
    These residual routes require pre-assessed eligibility. Existing benefit
    qualification approximations are inherited.
    """

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
                    "sda",
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
        # Para. 5(1)(a)(vi), as in Pension Credit: disability-related WTC
        # requires an actual award as well as a positive disability element.
        wtc_disability_element = (
            add(
                benunit,
                period,
                ["WTC_disabled_element", "WTC_severely_disabled_element"],
            )
            > 0
        ) & (benunit("working_tax_credit", period) > 0)
        pension = (
            benunit.any(
                person("is_claimant_or_partner", period)
                & (qualifying_receipt | person("is_blind", period))
            )
            | wtc_disability_element
            | (benunit("carer_premium", period) > 0)
        )
        # Working-age carer/occupation routes restrict which person's/job's
        # earnings may be disregarded. Do not automatically apply £20 to an
        # ordinary earner solely because their non-earning partner cares.
        return where(
            benunit("housing_benefit_pension_age_regulations_apply", period),
            pension,
            working,
        )
