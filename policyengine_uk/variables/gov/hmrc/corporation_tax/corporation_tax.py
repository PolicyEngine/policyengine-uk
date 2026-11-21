from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class corporation_tax(Variable):
    value_type = float
    entity = Firm
    label = "corporation tax"
    documentation = (
        "Corporation tax after setting the R&D expenditure credit against it. "
        "Any credit above the tax is shown in firm_rdec_excess_payable. "
        "The bank surcharge is a separate variable."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = "https://www.legislation.gov.uk/ukpga/2009/4/section/1042I"

    def formula(firm, period, parameters):
        tax = firm("corporation_tax_before_credits", period)
        credit = firm("firm_rd_expenditure_credit", period)
        return max_(tax - credit, 0)
