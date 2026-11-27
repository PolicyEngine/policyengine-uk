from policyengine_uk.model_api import *


class firm_small_profits_rate_excluded(Variable):
    value_type = bool
    entity = Firm
    label = "Firm excluded from the corporation tax small profits rate"
    documentation = (
        "Whether the company is barred from the small profits rate and "
        "marginal relief because it is a close investment-holding company "
        "(section 18N of the Corporation Tax Act 2010) or is not UK resident "
        "in the accounting period (sections 18A(1) and 18B(1)). Such a "
        "company pays the main rate on all its taxable total profits. "
        "Defaults to false."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/18A",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/18B",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/18N",
    )
