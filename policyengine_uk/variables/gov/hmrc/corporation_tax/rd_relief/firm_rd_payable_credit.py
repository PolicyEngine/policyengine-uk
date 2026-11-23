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
        "loss. For accounting periods beginning on or after 1 April 2021 the "
        "credit is the lesser of that amount and the cap by reference to PAYE "
        "and NIC liabilities: £20,000 plus three times the company's relevant "
        "expenditure on workers (section 1058(1A) and sections 1058A to "
        "1058C) and, from April 2024, its relevant PAYE and NIC liabilities "
        "(section 1112B). Both are PAYE income tax and Class 1 National "
        "Insurance on all employees, adjusted for workers provided by "
        "connected companies; supply them as "
        "firm_relevant_paye_nic_liabilities. The cap applies only when "
        "firm_rdec_paye_nic_cap_supplied is true; with the flag true and the "
        "input left at 0 the credit is at most £20,000. Leave the flag false "
        "for a company exempt from the cap because it creates or manages its "
        "own intellectual property (section 1058D, from April 2024 section "
        "1112E), which the model does not test. The proportionate reduction "
        "of the £20,000 for a period under 12 months is not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1058",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1058/2022-04-01",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1058A/2022-04-01",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1112B",
    )
    defined_for = "firm_claims_rd_sme_relief"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax.rd_relief
        rate = where(
            firm("firm_is_rd_intensive", period),
            p.sme.intensive_payable_credit_rate,
            p.sme.payable_credit_rate,
        )
        credit = rate * firm("firm_rd_surrenderable_loss", period)
        if not p.sme.payable_credit_paye_nic_cap_applies:
            return credit
        cap = p.paye_nic_cap.amount + p.paye_nic_cap.multiplier * firm(
            "firm_relevant_paye_nic_liabilities", period
        )
        supplied = firm("firm_rdec_paye_nic_cap_supplied", period)
        return where(supplied, min_(credit, cap), credit)
