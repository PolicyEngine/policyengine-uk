from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_exempt_distributions(Variable):
    value_type = float
    entity = Firm
    label = "Firm exempt distributions"
    documentation = (
        "Exempt distributions received from non-group companies, which are "
        "added to taxable total profits to give augmented profits for the "
        "small profits rate and marginal relief."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/18L"
