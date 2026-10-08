from policyengine_uk.model_api import *


class housing_benefit_non_dep_linked_inpatient_days(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "housing benefit non dep linked inpatient days"
    documentation = "Days actually spent as an inpatient in the current linked series of admissions. Sum admission days only, excluding intervening days; restart the series after any gap exceeding 28 days. Must be supplied from admission/discharge records, not elapsed time since the first admission."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )
