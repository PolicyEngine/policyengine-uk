from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_flat_rate_scheme_eligible(Variable):
    label = "Eligible for the VAT flat rate scheme"
    documentation = (
        "Whether the firm's taxable turnover, excluding VAT, is within the "
        "flat rate scheme joining limit. The joining test is applied to the "
        "year's turnover; the leaving test on VAT-inclusive turnover is not "
        "modelled."
    )
    entity = Firm
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/uksi/1995/2518/regulation/55L"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.vat.flat_rate
        turnover = firm("firm_vat_taxable_turnover", period)
        return turnover <= p.join_threshold
