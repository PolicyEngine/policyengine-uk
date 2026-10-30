from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_childcare_element import (
    hb_capped_childcare_charges,
)


class housing_benefit_wtc_disregard(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR
    unit = GBP
    label = "Housing Benefit Working Tax Credit disregard"
    documentation = (
        "Working Tax Credit disregarded before the childcare deduction when "
        "the additional-disregard work conditions hold but earnings cannot "
        "fund the additional earnings disregard. The amount is capped at "
        "WTC received and the statutory additional amount, using its dated "
        "history, including the temporary 2020 increase. The existing "
        "tax-credit active parameter suppresses it from fiscal year 2025. "
        "This is separate from the earnings-only disregard."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/56",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/40",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/5/paragraph/21",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/6/paragraph/58",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/6/paragraph/22",
        "https://www.legislation.gov.uk/uksi/2020/371/regulation/5",
        "https://www.legislation.gov.uk/nisr/2020/53/regulation/5",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp
        net = max_(benunit("housing_benefit_net_earnings", period), 0)
        standard = benunit(
            "housing_benefit_applied_standard_earnings_disregard", period
        )
        accommodation = min_(
            max_(
                benunit(
                    "housing_benefit_specified_or_temporary_accommodation_disregard",
                    period,
                ),
                0,
            ),
            max_(0, net - standard),
        )
        additional = (
            p.housing_benefit.means_test.income_disregard.worker * WEEKS_IN_YEAR
        )
        # Sch 4 para 17(3)(b) tests deductible childcare. If earnings cover
        # childcare plus the positive additional amount, all capped charges
        # already fit within earnings alone. Otherwise reducing the credit
        # pool cannot make the test pass: a limited deduction takes at least
        # all remaining earnings. Using the full charge therefore gives the
        # same test without a cycle through childcare and this WTC reserve.
        childcare = hb_capped_childcare_charges(benunit, period, parameters)
        covers_additional = np.round(net.astype(float), 2) >= np.round(
            (standard + accommodation + childcare + additional).astype(float), 2
        )
        applies = (
            p.tax_credits.active
            & benunit(
                "meets_housing_benefit_additional_earnings_disregard_conditions", period
            )
            & ~covers_additional
        )
        return where(
            applies,
            min_(max_(benunit("working_tax_credit", period), 0), additional),
            0,
        )
