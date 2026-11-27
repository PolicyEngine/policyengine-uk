from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class digital_services_tax(Variable):
    value_type = float
    entity = Firm
    label = "Digital services tax"
    documentation = (
        "Digital services tax from 1 April 2020 (Finance Act 2020 Part 2): "
        "where the group's worldwide digital services revenues exceed £500 "
        "million and its UK digital services revenues exceed £25 million "
        "(s.46), 2% of the group's UK revenues above £25 million, shared "
        "between members by their UK revenues (s.47). The group totals "
        "default to the firm's own UK revenues. Not modelled: the "
        "alternative charge for loss-making services (s.48) and the "
        "relief for cross-border marketplace transactions."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2020/14/section/46",
        "https://www.legislation.gov.uk/ukpga/2020/14/section/47",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.digital_services_tax
        own = max_(firm("firm_uk_digital_services_revenues", period), 0)
        group_uk = max_(firm("firm_group_uk_digital_services_revenues", period), own)
        group_world = max_(
            firm("firm_group_digital_services_revenues", period), group_uk
        )
        liable = (group_world > p.threshold.worldwide_revenues) & (
            group_uk > p.threshold.uk_revenues
        )
        share = np.divide(own, group_uk, out=np.zeros_like(own), where=group_uk > 0)
        tax = p.rate * max_(group_uk - p.allowance, 0) * share
        return where(liable, tax, 0)
