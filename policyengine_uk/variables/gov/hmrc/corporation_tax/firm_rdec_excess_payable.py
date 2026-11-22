from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_rdec_excess_payable(Variable):
    value_type = float
    entity = Firm
    label = "Firm R&D expenditure credit in excess of corporation tax"
    documentation = (
        "R&D expenditure credit treated as paid to the company for the year. "
        "Step 1 sets the credit against the year's corporation tax. Step 2 "
        "removes the notional tax deduction: what is left may not exceed the "
        "credit less corporation tax on the credit. Under the merged scheme "
        "(section 1042K) the rate is the main rate where the company has "
        "profits chargeable at the main rate ignoring the credit and the "
        "small profits rate otherwise; before April 2024 (section 104N) it is "
        "always the main rate. A company in the "
        "marginal relief band counts as charged at the main rate. Profits "
        "ignoring the credit are taxable total profits less the credit, "
        "with no recalculation of the carried-forward loss restriction. The "
        "notional tax deduction is not paid: it is set against later "
        "corporation tax or surrendered (section 1042L), which is not "
        "modelled. The PAYE and NIC cap of step 3 (section 1112B) is not "
        "modelled, for want of an input for PAYE and NIC on R&D staff, nor "
        "are set-off against other periods and liabilities and group "
        "surrender."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2009/4/section/104N/2024-03-31",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1042I",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1042K",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1042L",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax
        tax = firm("corporation_tax_before_credits", period)
        credit = firm("firm_rd_expenditure_credit", period)
        # Step 1: set the credit against the year's corporation tax.
        after_step_1 = max_(credit - tax, 0)
        # Step 2 (s.1042K, before April 2024 s.104N): the notional tax
        # deduction is the excess of the step 1 amount over the credit less
        # notional tax on the credit. s.104N uses the main rate throughout.
        merged = p.rd_relief.merged_scheme_in_effect
        if not (merged and p.small_profits_rate_applies):
            rate = p.main_rate
        else:
            taxable = firm("firm_taxable_profit", period)
            taxable_ex_credit = max_(taxable - credit, 0)
            augmented_ex_credit = firm("firm_augmented_profits", period) - (
                taxable - taxable_ex_credit
            )
            lower = firm("firm_corporation_tax_lower_limit", period)
            main_rate_profits = (taxable_ex_credit > 0) & (augmented_ex_credit > lower)
            rate = where(main_rate_profits, p.main_rate, p.small_profits_rate)
        return min_(after_step_1, credit * (1 - rate))
