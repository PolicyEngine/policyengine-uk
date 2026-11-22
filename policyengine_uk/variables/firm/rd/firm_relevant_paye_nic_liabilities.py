from policyengine_uk.model_api import *


class firm_relevant_paye_nic_liabilities(Variable):
    value_type = float
    entity = Firm
    label = "Firm relevant PAYE and NIC liabilities"
    documentation = (
        "Relevant PAYE and NIC liabilities for the merged R&D expenditure "
        "credit cap (sections 1112C and 1112D of the Corporation Tax Act "
        "2009): income tax under PAYE plus Class 1 National Insurance the "
        "company accounts for on all its employees for payment periods ending "
        "in the accounting period, plus or minus the amounts for workers and "
        "contractors provided by connected companies. Used from April 2024. "
        "Used only when firm_rdec_paye_nic_cap_supplied is true; "
        "leave it unset for a company exempt from the cap under section 1112E."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    default_value = 0
    reference = (
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1112C",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1112D",
    )
