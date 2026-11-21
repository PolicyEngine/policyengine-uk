from policyengine_uk.model_api import *


class firm_special_rate_pool_writing_down_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Firm special rate pool writing-down allowance"
    documentation = (
        "Writing-down allowance on the special rate pool of plant and machinery at the special rate. A pool of no more than the small pool limit is written off in "
        "full (section 56A of the Capital Allowances Act 2001)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/104D",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/56A",
    )

    def formula(firm, period, parameters):
        p = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.writing_down_allowance
        balance = max_(firm("firm_special_rate_pool_balance", period), 0)
        return where(balance <= p.small_pool_limit, balance, p.special_rate * balance)
