from policyengine_uk.model_api import *


class firm_off_payroll_deemed_payments(Variable):
    value_type = float
    entity = Firm
    label = "Firm off-payroll deemed direct payments"
    documentation = "Deemed direct payments the firm makes as the fee-payer under the off-payroll working rules: the chain payments for workers engaged through intermediaries, less VAT, materials and any expenses deducted (SI 2000/727 reg 17(1)). Not part of firm_paybill. A small private-sector client is outside the rules from April 2021, so leave this at 0 for one. Defaults to 0."
    definition_period = YEAR
    hidden_input = True
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2000/727/regulation/17"
