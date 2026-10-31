from policyengine_uk.model_api import *


class ebr_council_tax_rebate(Variable):
    label = "Council Tax Rebate (EBR)"
    documentation = (
        "Council Tax discount under the Energy Bills Rebate. English billing "
        "authorities paid the £150 Council Tax Rebate to households in bands A "
        "to D (billing authority guidance, paragraphs 2 and 11). Scottish "
        "councils paid the Cost of Living Award and Welsh councils the Cost of "
        "Living Support Scheme, £150 each, to bands A to D and to Council Tax "
        "Reduction recipients in any band (Local Government Finance Circular "
        "2/2022, paragraphs 6, 10 and 12; Welsh guide, conditions A and B). "
        "Northern Ireland levies domestic rates, not council tax, and had no "
        "Council Tax Rebate; its households received the £600 Energy Bills "
        "Support Scheme payment. Scottish councils tested receipt on 14 "
        "February 2022 and Welsh councils on 15 February 2022. The model reads "
        "council_tax_reduction for the whole year. Councils in all three "
        "nations also paid band E homes charged at band D under the disabled "
        "band reduction (England's paragraph 11(i), Scotland's paragraph 12, "
        "Wales's condition B). The model has no input for that reduction. In "
        "Scotland and Wales it pays those homes only when they also receive "
        "Council Tax Reduction; in England it never pays them. It has no "
        "council tax exemption input, so it can't apply Scotland's rules for "
        "exempt dwellings (paragraphs 15 to 18). It doesn't simulate second "
        "adult rebate or Scotland's separate Council Tax Reduction for bands E "
        "to H (regulation 14A, inserted by SSI 2016/253), so a Scottish "
        "household in band E or above on either alone misses the payment."
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
        # Scottish and Welsh councils also paid Council Tax Reduction recipients
        # in any band; English billing authorities paid by band alone.
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
