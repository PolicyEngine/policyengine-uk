from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat_registered(Variable):
    label = "Registered for VAT"
    documentation = (
        "Whether the firm is registered for VAT: its taxable turnover in the "
        "year exceeds the registration threshold, or it registers voluntarily. "
        "The test uses the year's turnover and the threshold in force on 30 "
        "April of the year (so 2024 uses the £90,000 threshold from 1 April "
        "2024), not a rolling 12-month look-back."
    )
    entity = Firm
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/ukpga/1994/23/schedule/1/paragraph/1"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.vat.registration
        turnover = firm("firm_vat_taxable_turnover", period)
        voluntary = firm("firm_vat_voluntarily_registered", period)
        return (turnover > p.threshold) | voluntary
