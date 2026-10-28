from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import MONTHS_FROM_TAX_YEAR_START_TO_MID_YEAR
from policyengine_uk.utils.income_tax_reductions import earlier_tax_reductions


class pension_tax_allowance(Variable):
    value_type = float
    entity = Person
    label = "Pension Tax Allowance"
    documentation = (
        "Income Tax reduction for people over State Pension age or reaching it "
        "in the tax year, from 2027-28 to 2029-30. The full allowance is 20% of "
        "the full new State Pension above the Personal Allowance, rounded up to "
        "the pound (£94 in 2027-28). It falls by £1 for every £3 of total "
        "income above the full new State Pension. It is non-refundable: it is "
        "deducted at Step 6 after the reductions listed before it in "
        "income_tax_subtractions, only so far as there is Step 5 tax left, "
        "and it does not change the Personal Allowance."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Budget 2026, paragraph 6.182",
            href="https://assets.publishing.service.gov.uk/media/6ae1ec57bdb574cf1c9b3f12/E03668986_HMT_Budget_2026_ELAY__2_.pdf#page=135",
        ),
        dict(
            title="HM Treasury, Pension Tax Allowance explainer",
            href="https://www.gov.uk/government/publications/pension-tax-allowance-explainer/pension-tax-allowance-explainer",
        ),
        dict(
            title="Income Tax Act 2007, s. 23 (Step 6) and s. 29(2)-(3)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
        ),
    ]

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        p = income_tax.reliefs.pension_tax_allowance
        threshold = p.state_pension_threshold
        personal_allowance = income_tax.allowances.personal_allowance.amount
        # The explainer rounds 20% of £466.40 (£93.28) up to £94, and tapers
        # from £94: Jonathan, £150 above the threshold, gets £94 - £50 = £44.
        # Rounding to a millionth first keeps a whole-pound value whole.
        full = np.ceil(np.round(p.rate * max_(0, threshold - personal_allowance), 6))
        excess = max_(0, person("total_income", period) - threshold)
        allowance = max_(0, full - p.taper * excess)
        # Over State Pension age or reaching it within the tax year: attaining
        # it before 6 April of the next year, six months after 6 October.
        eligible = (
            person("months_since_state_pension_age", period)
            > -MONTHS_FROM_TAX_YEAR_START_TO_MID_YEAR
        )
        earlier = earlier_tax_reductions(income_tax, "pension_tax_allowance")
        tax_left = max_(
            0,
            person("income_tax_pre_charges", period) - add(person, period, earlier),
        )
        return p.in_effect * eligible * min_(allowance, tax_left)
