from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class bank_surcharge(Variable):
    value_type = float
    entity = Firm
    label = "bank corporation tax surcharge"
    documentation = (
        "Surcharge on a banking company's surcharge profits above the "
        "surcharge allowance. Surcharge profits are approximated by taxable "
        "total profits: the add-back of group relief and of losses from "
        "non-banking companies is ignored, and the company is given the "
        "whole allowance. The rate is the one in force on 30 April of the "
        "financial year, so changes part-way through a financial year (the "
        "6% rate from 1 January 2027) are not apportioned."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269DA",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269DJ",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.bank_surcharge
        is_bank = firm("firm_is_bank", period)
        profits = firm("firm_taxable_profit", period)
        surcharge = p.rate * max_(profits - p.allowance, 0)
        return where(is_bank, surcharge, 0)
