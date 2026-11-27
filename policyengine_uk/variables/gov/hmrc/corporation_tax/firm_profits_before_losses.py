from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_profits_before_losses(Variable):
    value_type = float
    entity = Firm
    label = "Firm profits before losses brought forward"
    documentation = (
        "Taxable trading profit less capital allowances and the R&D "
        "additional deduction, plus the taxable R&D expenditure credit and "
        "non-trading profits, less the Patent Box deduction. Negative when the "
        "firm makes a loss in the year."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/4"

    def formula(firm, period, parameters):
        return firm("firm_profits_before_patent_box", period) - firm(
            "firm_patent_box_deduction", period
        )
