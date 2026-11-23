from policyengine_uk.model_api import *


class firm_capex_special_rate_new(Variable):
    value_type = float
    entity = Firm
    label = "Firm new special-rate plant and machinery expenditure"
    documentation = "Expenditure in the year on unused, not second-hand special rate plant and machinery, such as integral features and long-life assets. Excludes cars. Special-rate plant for leasing gets no first-year allowance (general exclusion 6 in section 46(2) of the Capital Allowances Act 2001 bars section 45S, and section 45U(b) excludes special rate expenditure), but this input would give it the 50% allowance; enter it as firm_capex_special_rate_used instead, which takes the annual investment allowance and then the special rate pool."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
