from policyengine_uk.model_api import *


class firm_rd_payable_credit(Variable):
    value_type = float
    entity = Firm
    label = "Firm R&D payable tax credit"
    documentation = (
        "Payable R&D tax credit for surrendering the surrenderable loss under "
        "section 1058 of the Corporation Tax Act 2009, at the R&D intensive "
        "rate for an R&D intensive SME and the general SME rate otherwise. "
        "Assumes every eligible company surrenders its whole surrenderable "
        "loss. The PAYE and National Insurance cap is not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2009/4/section/1058"
    defined_for = "firm_claims_rd_sme_relief"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax.rd_relief.sme
        rate = where(
            firm("firm_is_rd_intensive", period),
            p.intensive_payable_credit_rate,
            p.payable_credit_rate,
        )
        return rate * firm("firm_rd_surrenderable_loss", period)
