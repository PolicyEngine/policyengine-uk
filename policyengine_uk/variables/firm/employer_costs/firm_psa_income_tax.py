from policyengine_uk.model_api import *


class firm_psa_income_tax(Variable):
    value_type = float
    entity = Firm
    label = "Firm PAYE settlement agreement income tax"
    documentation = "Total income tax, grossed up, for which the firm is accountable under its PAYE settlement agreements (SSCBA 1992 s.10A(1)(b)). Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/10A"
