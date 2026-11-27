from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_recoverable_input_vat(Variable):
    label = "Recoverable input VAT"
    documentation = (
        "Input VAT the firm can deduct from output VAT after the partial "
        "exemption restriction (SI 1995/2518 reg 101(2)): input VAT directly "
        "attributable to taxable supplies in full, none of that directly "
        "attributable to exempt supplies, and the residual input VAT at "
        "firm_partial_exemption_recovery_share. With the attribution inputs "
        "at their default of 0, all input VAT is residual. Where "
        "firm_applies_partial_exemption_de_minimis is true and either de "
        "minimis test is met over the year, all input VAT is recoverable: "
        "the reg 106 test (exempt input tax at most £625 a month on average "
        "and at most half of all input tax) or, from 1 April 2010, the reg "
        "105A simplified test (input tax less that used exclusively for "
        "taxable supplies at most £625 a month on average, with exempt "
        "supplies at most half of all supplies). Exempt input tax is the "
        "directly attributable exempt part plus the unrecovered share of "
        "residual input tax. The tests are applied to the whole year, as in "
        "the annual adjustment (reg 107); the provisional reg 106ZA "
        "annual test is not modelled, since it does not change the year's "
        "liability. Boundaries are inclusive. The tests are not applied "
        "where input VAT is zero or negative."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ukpga/1994/23/section/26",
        "https://www.legislation.gov.uk/uksi/1995/2518/regulation/101",
        "https://www.legislation.gov.uk/uksi/1995/2518/regulation/105A",
        "https://www.legislation.gov.uk/uksi/1995/2518/regulation/106",
        "https://www.legislation.gov.uk/uksi/1995/2518/regulation/107",
    ]

    def formula(firm, period, parameters):
        input_vat = firm("firm_input_vat", period)
        taxable_direct = min_(
            max_(firm("firm_input_vat_attributable_to_taxable_supplies", period), 0),
            max_(input_vat, 0),
        )
        exempt_direct = min_(
            max_(firm("firm_input_vat_attributable_to_exempt_supplies", period), 0),
            max_(input_vat - taxable_direct, 0),
        )
        residual = input_vat - taxable_direct - exempt_direct
        share = firm("firm_partial_exemption_recovery_share", period)
        standard_method = taxable_direct + residual * share
        p = parameters(period).gov.hmrc.vat.partial_exemption.de_minimis
        exempt_input = exempt_direct + residual * (1 - share)
        original_test = (exempt_input <= p.monthly_limit * MONTHS_IN_YEAR) & (
            exempt_input <= p.input_tax_share * input_vat
        )
        simplified = p.simplified
        if simplified.in_effect:
            exempt_supplies = firm("firm_exempt_supplies", period)
            all_supplies = firm("firm_vat_taxable_turnover", period) + exempt_supplies
            simplified_test = (
                input_vat - taxable_direct <= simplified.monthly_limit * MONTHS_IN_YEAR
            ) & (exempt_supplies <= simplified.exempt_supplies_share * all_supplies)
        else:
            simplified_test = np.zeros(firm.count, dtype=bool)
        de_minimis = (
            firm("firm_applies_partial_exemption_de_minimis", period)
            & (input_vat > 0)
            & (original_test | simplified_test)
        )
        return where(de_minimis, input_vat, standard_method)
