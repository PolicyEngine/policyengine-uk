from policyengine_uk.model_api import *


class firm_rd_staff_paye_nic(Variable):
    value_type = float
    entity = Firm
    label = "Firm PAYE and NIC on R&D staff"
    documentation = (
        "Total expenditure on workers for the R&D expenditure credit cap "
        "before April 2024 (section 104P of the Corporation Tax Act 2009 as "
        "at 31 March 2024): staffing costs of directors and employees directly "
        "and actively engaged in R&D that form part of the company's PAYE "
        "income tax and Class 1 National Insurance liabilities, plus the "
        "relevant portion for externally provided workers from other group "
        "members. Used only when firm_rdec_paye_nic_cap_supplied is true."
    )
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    default_value = 0
    reference = (
        "https://www.legislation.gov.uk/ukpga/2009/4/section/104P/2024-03-31",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/104Q/2024-03-31",
    )
