from policyengine_uk.model_api import *


class firm_main_pool_writing_down_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Firm main pool writing-down allowance"
    documentation = (
        "Writing-down allowance on the main pool of plant and machinery at the main rate. A pool of no more than the small pool limit is written off in "
        "full (section 56A of the Capital Allowances Act 2001)."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/56",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/56A",
    )

    def formula(firm, period, parameters):
        p = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.writing_down_allowance
        balance = max_(firm("firm_main_pool_balance", period), 0)
        return where(balance <= p.small_pool_limit, balance, p.main_rate * balance)
