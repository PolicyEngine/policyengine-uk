from policyengine_uk.model_api import *
from policyengine_uk.utils.lha import benunit_lha


class uncapped_BRMA_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "LHA percentile rent"
    documentation = (
        "Weekly rent at the LHA percentile (30th by default) of the Broad Rental "
        "Market Area's list of rents for the benefit unit's LHA category, in the "
        "year whose determination is in force, annualised over 52 weeks. This is "
        "before the national maximum, the anomalous-rate rule and the March 2020 "
        "minimum."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1997/1984/schedule/3B",
        "https://www.gov.uk/government/collections/local-housing-allowance-lha-rates",
    ]

    def formula(benunit, period, parameters):
        return benunit_lha(benunit, period, "percentile") * WEEKS_IN_YEAR
