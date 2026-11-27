from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_patent_box_deduction(Variable):
    value_type = float
    entity = Firm
    label = "Firm Patent Box deduction"
    documentation = (
        "The Patent Box deduction from trading profits (CTA 2010 s.357A): "
        "relevant IP profits times (applicable rate less the special IP "
        "rate) over the applicable rate, so that the profits are taxed at "
        "the special IP rate of 10%. Relevant IP profits are brought in at "
        "60% in the financial year 2013, rising to 100% from 1 April 2017 "
        "(FA 2012 Sch 2 para 8). As a model guard, not statute, they are "
        "capped at the positive trading profit after capital allowances and "
        "the R&D additional deduction. Relevant IP losses and the "
        "set-off of losses between periods (ss.357E-357EF) are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/357A",
        "https://www.legislation.gov.uk/ukpga/2012/14/schedule/2/paragraph/8",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax.patent_box
        share = p.relevant_ip_profits_share
        if share == 0:
            return np.zeros(firm.count)
        trading = max_(
            firm("firm_taxable_trading_profit", period)
            - firm("firm_capital_allowances", period)
            - firm("firm_rd_additional_deduction", period),
            0,
        )
        relevant = min_(max_(firm("firm_relevant_ip_profits", period), 0), trading)
        rate = firm("firm_patent_box_applicable_rate", period)
        fraction = np.divide(
            max_(rate - p.special_ip_rate, 0),
            rate,
            out=np.zeros_like(rate),
            where=rate > 0,
        )
        return share * relevant * fraction
