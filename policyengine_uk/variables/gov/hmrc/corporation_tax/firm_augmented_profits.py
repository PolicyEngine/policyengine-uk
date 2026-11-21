from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_augmented_profits(Variable):
    value_type = float
    entity = Firm
    label = "firm augmented profits"
    documentation = (
        "Taxable total profits plus exempt distributions from non-group "
        "companies, compared with the lower and upper limits."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/18L"
    adds = ["firm_taxable_profit", "firm_exempt_distributions"]
