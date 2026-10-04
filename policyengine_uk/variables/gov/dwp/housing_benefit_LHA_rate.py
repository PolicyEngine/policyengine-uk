from policyengine_uk.model_api import *
from policyengine_uk.utils.lha import benunit_lha


class housing_benefit_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "LHA rate (Housing Benefit)"
    documentation = (
        "The Local Housing Allowance for the Housing Benefit category of "
        "dwelling: the weekly rate determined for the Broad Rental Market "
        "Area and category, annualised over 52 weeks."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/1997/1984/schedule/3B",
        "https://www.gov.uk/government/collections/local-housing-allowance-lha-rates",
    )

    def formula(benunit, period, parameters):
        """The determined Housing Benefit rate for the HB category.

        The same determination as ``BRMA_LHA_rate`` (the lower of the BRMA
        percentile rent and the weekly national maximum, the anomalous-rate
        rule and, from April 2024, the 31 March 2020 minimum: Rent Officers
        (Housing Benefit Functions) Order 1997, Schedule 3B paragraphs 2, 3
        and 3A), read for the category in HB Regulations 2006 reg 13D rather
        than the Universal Credit one.
        """
        return (
            benunit_lha(
                benunit,
                period,
                "rate",
                category_variable="housing_benefit_LHA_category",
            )
            * WEEKS_IN_YEAR
        )
