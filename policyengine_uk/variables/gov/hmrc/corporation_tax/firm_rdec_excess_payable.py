from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_rdec_excess_payable(Variable):
    value_type = float
    entity = Firm
    label = "firm R&D expenditure credit in excess of corporation tax"
    documentation = (
        "R&D expenditure credit left after discharging the year's corporation "
        "tax, treated as paid to the company. The notional tax deduction, the "
        "PAYE and NIC cap and set-off against other liabilities in the "
        "statutory payment steps are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = "https://www.legislation.gov.uk/ukpga/2009/4/section/1042I"

    def formula(firm, period, parameters):
        tax = firm("corporation_tax_before_credits", period)
        credit = firm("firm_rd_expenditure_credit", period)
        return max_(credit - tax, 0)
