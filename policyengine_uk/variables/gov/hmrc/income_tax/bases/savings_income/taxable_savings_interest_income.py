from policyengine_uk.model_api import *


class taxable_savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of savings interest which is taxable"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act (Trading and Other Income) 2005, s. 369",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/369",
    )
    unit = GBP

    def formula(person, period, parameters):
        standard_interest = person("savings_interest_income", period)
        other_interest = person("other_investment_income", period)
        # Zero unless a reform sets the cash ISA excess response: interest on
        # cash a cash ISA limit keeps out, held in taxable savings instead.
        displaced_interest = person("cash_isa_excess_savings_interest", period)
        total_interest = standard_interest + other_interest + displaced_interest
        # Exempt interest is a separate additive input, not an allowance
        # against interest from unrelated taxable savings.
        return max_(0, total_interest)
