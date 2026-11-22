from policyengine_uk.model_api import *


class apprenticeship_levy(Variable):
    value_type = float
    entity = Firm
    label = "Apprenticeship levy"
    documentation = (
        "The relevant percentage of the firm's pay bill, less its levy "
        "allowance, floored at zero (Finance Act 2016 s.99). The pay bill is "
        "all earnings on which the firm incurs secondary Class 1 liabilities, "
        "including earnings below the secondary threshold (s.100(3)) and "
        "earnings zero-rated at £0 (s.100(6)), so it is "
        "firm_paybill_after_minimum_wage: firm_paybill plus any pay needed to "
        "meet the minimum wage. A member of a company unit of connected companies receives its allocated share of "
        "one allowance (s.101)."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Finance Act 2016 s.99",
            href="https://www.legislation.gov.uk/ukpga/2016/24/section/99",
        ),
        dict(
            title="Finance Act 2016 s.100(2), (3) and (6)",
            href="https://www.legislation.gov.uk/ukpga/2016/24/section/100",
        ),
        dict(
            title="Finance Act 2016 s.101",
            href="https://www.legislation.gov.uk/ukpga/2016/24/section/101",
        ),
    ]

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.apprenticeship_levy
        paybill = firm("firm_paybill_after_minimum_wage", period)
        share = firm("firm_apprenticeship_levy_allowance_share", period)
        return max_(p.rate * paybill - p.allowance * share, 0)
