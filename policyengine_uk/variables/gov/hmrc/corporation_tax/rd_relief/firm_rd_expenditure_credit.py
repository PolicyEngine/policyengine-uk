from policyengine_uk.model_api import *


class firm_rd_expenditure_credit(Variable):
    value_type = float
    entity = Firm
    label = "Firm R&D expenditure credit"
    documentation = (
        "R&D expenditure credit on qualifying expenditure for a company that "
        "does not claim SME relief: the merged scheme credit from April 2024 "
        "and the large-company credit before. The credit is a taxable receipt "
        "of the trade and is set against corporation tax. The notional tax "
        "deduction, the PAYE cap and payment steps for loss-makers are not "
        "modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1042G",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/104M",
    )

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.rd_relief.expenditure_credit.rate
        is_company = (
            firm("firm_legal_form", period)
            == firm("firm_legal_form", period).possible_values.COMPANY
        )
        eligible = is_company & ~firm("firm_claims_rd_sme_relief", period)
        return where(eligible, rate * firm("firm_qualifying_rd_expenditure", period), 0)
