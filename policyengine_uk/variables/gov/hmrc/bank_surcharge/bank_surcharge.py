from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class bank_surcharge(Variable):
    value_type = float
    entity = Firm
    label = "Bank corporation tax surcharge"
    documentation = (
        "Surcharge on a banking company's surcharge profits above its "
        "surcharge allowance. Surcharge profits are taxable total profits "
        "plus group relief surrendered by non-banking companies "
        "(firm_non_banking_group_relief_claimed, capped at the group relief "
        "given), less the R&D expenditure credit brought in as a receipt of "
        "the trade (s.269DA). Not modelled: the add-back of carried-forward "
        "losses from non-banking or pre-2016 periods (s.269DC), the 25% cap "
        "on a bank's pre-April 2015 trading losses (s.269CA), and the "
        "transferred gains adjustments. A "
        "company in a group with other banking companies receives the share "
        "of the allowance in firm_bank_surcharge_allowance_share. The rate is "
        "day-weighted over each 6 April to 5 April year, approximating the "
        "split of an accounting period that straddles a rate change such as "
        "the 6% rate from 1 January 2027."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269DA",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269DE",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269DJ",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.bank_surcharge
        is_bank = firm("firm_is_bank", period)
        # s.269DA(2) deducts the RDEC brought into account as a receipt.
        # s.269DA(2) and s.269DB add back group relief surrendered by
        # non-banking companies.
        group_relief = add(
            firm,
            period,
            ["firm_group_relief", "firm_group_relief_for_carried_forward_losses"],
        )
        non_banking = min_(
            max_(firm("firm_non_banking_group_relief_claimed", period), 0),
            group_relief,
        )
        profits = max_(
            firm("firm_taxable_profit", period)
            + non_banking
            - firm("firm_rd_expenditure_credit", period),
            0,
        )
        allowance = p.allowance * firm("firm_bank_surcharge_allowance_share", period)
        surcharge = p.rate * max_(profits - allowance, 0)
        return where(is_bank, surcharge, 0)
