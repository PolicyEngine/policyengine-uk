from policyengine_uk.model_api import *


class firm_claims_rd_sme_relief(Variable):
    value_type = bool
    entity = Firm
    label = "Firm claims SME R&D relief"
    documentation = (
        "Whether the firm claims R&D relief under Chapter 2 of Part 13 of the "
        "Corporation Tax Act 2009 rather than the R&D expenditure credit. "
        "Before April 2024 every SME company with qualifying expenditure did. "
        "From April 2024 only an SME company that is R&D intensive and makes a "
        "trading loss before the additional deduction (enhanced R&D intensive "
        "support) does. The trading loss is trading profit less capital "
        "allowances."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1044",
        "https://www.gov.uk/hmrc-internal-manuals/corporate-intangibles-research-and-development-manual/cird121000",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax.rd_relief
        is_company = (
            firm("firm_legal_form", period)
            == firm("firm_legal_form", period).possible_values.COMPANY
        )
        sme_with_rd = (
            is_company
            & firm("firm_is_sme", period)
            & (firm("firm_qualifying_rd_expenditure", period) > 0)
        )
        if not p.merged_scheme_in_effect:
            return sme_with_rd
        profit_before_deduction = firm("firm_taxable_trading_profit", period) - firm(
            "firm_capital_allowances", period
        )
        return (
            sme_with_rd
            & firm("firm_is_rd_intensive", period)
            & (profit_before_deduction < 0)
        )
