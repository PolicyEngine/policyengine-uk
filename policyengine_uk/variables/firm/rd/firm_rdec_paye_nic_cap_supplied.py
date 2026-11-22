from policyengine_uk.model_api import *


class firm_rdec_paye_nic_cap_supplied(Variable):
    value_type = bool
    entity = Firm
    label = "Firm PAYE and NIC figures for the RDEC cap are supplied"
    documentation = (
        "Whether firm_relevant_paye_nic_liabilities (from April 2024) or "
        "firm_rd_staff_paye_nic (before) is supplied, so the PAYE and NIC "
        "cap on the payable R&D expenditure credit applies. Defaults to "
        "false: no cap. Set the matching input too: with the flag true and "
        "the input at 0 the cap is nil before April 2024 and £20,000 after. Leave it false for a company exempt from the cap "
        "under section 1112E of the Corporation Tax Act 2009."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = False
