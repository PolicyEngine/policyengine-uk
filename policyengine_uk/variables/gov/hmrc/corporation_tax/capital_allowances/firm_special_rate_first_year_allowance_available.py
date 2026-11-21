from policyengine_uk.model_api import *


class firm_special_rate_first_year_allowance_available(Variable):
    value_type = bool
    entity = Firm
    label = "Firm can claim the special-rate first-year allowance"
    documentation = (
        "Whether the firm is a company and a first-year allowance on new "
        "special-rate plant and machinery is in force."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/45S"

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances.special_rate
        legal_form = firm("firm_legal_form", period)
        is_company = legal_form == legal_form.possible_values.COMPANY
        return is_company & (rate > 0)
