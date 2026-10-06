from policyengine_uk.model_api import *
from policyengine_uk.utils.lha import benunit_lha


class uc_LHA_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount for LHA under Universal Credit"
    documentation = "Rent covered by the Local Housing Allowance for Universal Credit"
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/382/schedule/1",
        "https://www.gov.uk/government/collections/universal-credit-local-housing-allowance-rates",
    ]

    def formula(benunit, period, parameters):
        """Universal Credit uses a monthly LHA determination.

        Schedule 1 to the Rent Officers (Universal Credit Functions) Order 2013
        determines monthly rates from monthly rents, with monthly national
        maxima set independently of the weekly Housing Benefit ones, so the
        weekly rate is not simply annualised. Before April 2020 the published
        monthly rates are used as they stand.
        """
        rent = benunit("benunit_rent", period)
        monthly = benunit_lha(benunit, period, "rate", universal_credit=True)
        return min_(rent, monthly * MONTHS_IN_YEAR)
