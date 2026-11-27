from policyengine_uk.model_api import *


class firm_rd_additional_deduction(Variable):
    value_type = float
    entity = Firm
    label = "Firm R&D additional deduction"
    documentation = (
        "Additional deduction in computing trading profits for qualifying R&D "
        "expenditure under section 1044 of the Corporation Tax Act 2009: the "
        "SME scheme before April 2024 and enhanced R&D intensive support from "
        "then. Deduct from trading profit on top of the expenditure itself."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2009/4/section/1044"
    defined_for = "firm_claims_rd_sme_relief"

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.rd_relief.sme.additional_deduction_rate
        return rate * firm("firm_qualifying_rd_expenditure", period)
