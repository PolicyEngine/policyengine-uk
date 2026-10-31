from policyengine_uk.model_api import *


class ebr_council_tax_rebate(Variable):
    label = "Council Tax Rebate (EBR)"
    documentation = (
        "Council Tax discount under the Energy Bills Rebate. England's £150 "
        "Council Tax Rebate went to households in bands A to D (billing "
        "authority guidance, paragraphs 2 and 11). Scotland's Cost of Living "
        "Award and Wales's Cost of Living Support Scheme paid £150 to bands A "
        "to D and to Council Tax Reduction recipients in any band (Local "
        "Government Finance Circular 2/2022, paragraphs 6, 10 and 12; Welsh "
        "guide, conditions A and B). Northern Ireland levies domestic rates, "
        "not council tax, and had no Council Tax Rebate; its households "
        "received the £600 Energy Bills Support Scheme payment. The test "
        "reads council_tax_reduction for the year, not receipt on 14 February "
        "2022 (Scotland) or 15 February 2022 (Wales). The model has no input "
        "for the disabled band reduction, so it doesn't pay band E homes "
        "charged at band D (England's paragraph 11(i), Scotland's paragraph "
        "12, Wales's condition B) unless they qualify through Council Tax "
        "Reduction. It also leaves out Scotland's payments to exempt dwellings "
        "(paragraphs 16 to 18), and second adult rebate, which it doesn't "
        "simulate."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.gov.uk/government/publications/the-council-tax-rebate-2022-23-billing-authority-guidance/support-for-energy-bills-the-council-tax-rebate-2022-23-billing-authority-guidance",
        "https://www.gov.scot/publications/local-government-finance-circular-2-2022-guidance-to-local-authorities-april-2022-cost-of-living-award/",
        "https://www.gov.wales/cost-living-support-scheme-guide-local-authorities-html",
        "https://www.legislation.gov.uk/nisi/1977/2157/contents",
    )

    def formula(household, period, parameters):
        p = parameters(period).gov.treasury.energy_bills_rebate.council_tax_rebate
        ct_band = household("council_tax_band", period)
        ct_band_values = ct_band.possible_values
        in_qualifying_band = np.any(
            np.array([ct_band == getattr(ct_band_values, band) for band in p.bands]),
            axis=0,
        )
        # Scotland and Wales also paid Council Tax Reduction recipients in any
        # band; England went by band alone.
        country = household("country", period)
        pays_reduction_recipients = np.isin(
            country.decode_to_str(), list(p.council_tax_reduction_countries)
        )
        receives_reduction = household("council_tax_reduction", period) > 0
        eligible = in_qualifying_band | (pays_reduction_recipients & receives_reduction)
        # Northern Ireland has no council tax bands, so its input band means
        # nothing here (the enhanced FRS gives every NI household band A).
        has_council_tax = country != country.possible_values.NORTHERN_IRELAND
        return has_council_tax * eligible * p.amount
