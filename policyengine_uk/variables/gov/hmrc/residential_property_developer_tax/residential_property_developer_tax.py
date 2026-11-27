from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class residential_property_developer_tax(Variable):
    value_type = float
    entity = Firm
    label = "Residential property developer tax"
    documentation = (
        "Residential property developer tax: 4% of the company's RPD "
        "profits so far as they exceed its share of the £25 million "
        "allowance (Finance Act 2022 ss.33 and 43), for accounting periods "
        "beginning on or after 1 April 2022. Companies only. It is not deductible for "
        "corporation tax (Sch 9 para 1), so corporation tax is unchanged. "
        "Not modelled: the derivation of RPD profits, RPDT reliefs, joint "
        "ventures and the exit charge for non-profit housing companies."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2022/3/section/33",
        "https://www.legislation.gov.uk/ukpga/2022/3/section/43",
        "https://www.legislation.gov.uk/ukpga/2022/3/schedule/9",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.residential_property_developer_tax
        profits = firm("firm_rpd_profits", period)
        share = clip(firm("firm_rpdt_allowance_share", period), 0, 1)
        return p.rate * max_(profits - p.allowance * share, 0)
