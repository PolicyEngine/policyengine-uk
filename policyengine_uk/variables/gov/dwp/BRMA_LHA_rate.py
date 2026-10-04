from policyengine_uk.model_api import *
from policyengine_uk.utils.lha import benunit_lha


class BRMA_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "LHA rate"
    documentation = (
        "Weekly Housing Benefit Local Housing Allowance for the benefit unit's "
        "Broad Rental Market Area and LHA category, annualised over 52 weeks"
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1997/1984/schedule/3B",
        "https://www.gov.uk/government/collections/local-housing-allowance-lha-rates",
    ]

    def formula(benunit, period, parameters):
        """The determined Housing Benefit rate.

        The lower of the BRMA percentile rent and the weekly national maximum,
        raised to the rate of any smaller category and, from April 2024, to the
        rate determined on 31 March 2020 (Rent Officers (Housing Benefit
        Functions) Order 1997, Schedule 3B paragraphs 2, 3 and 3A). Universal
        Credit has its own monthly determination: see ``uc_LHA_cap``.
        """
        return benunit_lha(benunit, period, "rate") * WEEKS_IN_YEAR
