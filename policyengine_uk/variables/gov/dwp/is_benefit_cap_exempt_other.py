from policyengine_uk.model_api import *


class is_benefit_cap_exempt_other(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap for non-health/disability reasons"
    definition_period = YEAR
    reference = (
        "https://www.gov.uk/benefit-cap/when-youre-not-affected",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/79",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/83",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60C",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75A",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/5",
    )

    def formula(benunit, period, parameters):
        # The benefit cap applies to a Universal Credit award whatever the
        # claimants' ages (UC Regs 2013 regs 79, 82 and 83), including a
        # mixed-age couple's joint award (reg 3(2)(a)). The one age-based
        # exception, SI 2014/1230 reg 60C (NI: SR 2016/226 reg 61C), covers
        # only claims where every claimant has reached the qualifying age for
        # State Pension Credit. The cap also applies to Housing Benefit under
        # the working-age regulations (HB Regs 2006 Part 8A). Housing Benefit
        # under the pension-age regulations, which never apply to a family on
        # Universal Credit, has no cap.
        pension_age_housing_benefit = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )

        # Check for Armed Forces Compensation Scheme payments
        afcs = benunit("afcs", period) > 0

        # ESA contribution-based with support component
        esa_support_component = benunit("esa_contrib", period) > 0

        return pension_age_housing_benefit | afcs | esa_support_component
