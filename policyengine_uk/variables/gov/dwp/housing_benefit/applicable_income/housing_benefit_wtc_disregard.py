from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import supplied_input
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_childcare_element import (
    hb_capped_childcare_charges,
    housing_benefit_applicable_income_childcare_element,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_childcare_earnings_limit import (
    housing_benefit_childcare_earnings_limit,
)


def hb_childcare_deduction_replaced(benunit, period):
    """Whether the childcare deduction differs from the model's own
    calculation: it, or the limit it reads, is supplied (by a dataset,
    set_input or a scenario), neutralized, or calculated by a formula a
    reform put in place of the model's."""
    system = benunit.simulation.tax_benefit_system
    for model_variable in (
        housing_benefit_applicable_income_childcare_element,
        housing_benefit_childcare_earnings_limit,
    ):
        name = model_variable.__name__
        variable = system.get_variable(name)
        formula = variable.get_formula(period)
        if (
            variable.is_neutralized
            or formula is None
            or formula.__code__ != model_variable.formula.__code__
            or supplied_input(benunit, name, period) is not None
        ):
            return True
    return False


def hb_wtc_disregard(benunit, period, parameters, accommodation=None):
    """WTC disregarded under Sch 5 para 56, given the full accommodation
    amount (by default the annual variable)."""
    p = parameters(period).gov.dwp
    if not p.tax_credits.active:
        return benunit.empty_array()
    net = benunit("housing_benefit_net_earnings", period)
    standard = benunit("housing_benefit_applied_standard_earnings_disregard", period)
    # Para 18 takes only the earnings the other disregards leave, but a cap
    # would not change this test: where it binds, earnings fall short of the
    # additional amount anyway.
    if accommodation is None:
        accommodation = benunit(
            "housing_benefit_specified_or_temporary_accommodation_disregard", period
        )
    additional = p.housing_benefit.means_test.income_disregard.worker * WEEKS_IN_YEAR
    # Sch 4 para 17(3)(b) counts the deductible childcare, which reg
    # 27(1)(c) takes from earnings and then from the credits this disregard
    # reduces. With the model's own deduction, the lesser of the capped
    # charge and the earnings and tax-credit limit, the whole capped charge
    # gives the same answer: if earnings cover it and the additional amount,
    # the whole charge fits within earnings; if not, a deduction the limit
    # caps takes at least all remaining earnings, so the test fails whatever
    # credits remain. That holds only for that formula. A supplied,
    # neutralized or replaced deduction or limit can differ, so the test
    # then reads the deduction the earnings disregard reads. A replacement
    # that itself reads the limit depends on this disregard, and the engine
    # stops with a circular-definition error.
    if hb_childcare_deduction_replaced(benunit, period):
        childcare = benunit(
            "housing_benefit_applicable_income_childcare_element", period
        )
    else:
        childcare = hb_capped_childcare_charges(benunit, period, parameters)
    covers_additional = np.round(net.astype(float), 2) >= np.round(
        (standard + accommodation + childcare + additional).astype(float), 2
    )
    applies = (
        benunit(
            "meets_housing_benefit_additional_earnings_disregard_conditions", period
        )
        & ~covers_additional
    )
    return where(
        applies,
        min_(max_(benunit("working_tax_credit", period), 0), additional),
        0,
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
        "This is separate from the earnings-only disregard. Where the "
        "childcare deduction or its limit is supplied, neutralized or "
        "replaced, the earnings test reads the same deduction as the "
        "earnings disregard, so the two additional disregards never both "
        "apply."
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
        return hb_wtc_disregard(benunit, period, parameters)
