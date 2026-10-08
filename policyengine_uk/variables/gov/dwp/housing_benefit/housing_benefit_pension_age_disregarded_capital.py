from policyengine_uk.model_api import *
from policyengine_uk.utils.housing_benefit_capital import disregarded_capital


class housing_benefit_pension_age_disregarded_capital(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    label = "pension age Housing Benefit capital exclusions within supplied assets"
    documentation = "Category-specific retained capital exclusions. Inputs must be present in the assessed sources, disjoint, and supported by their statutory provenance/date/occupation/business facts. This does not infer those facts from broad survey balances or implement every separately listed historic compensation scheme."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/uksi/2026/681",
        "https://www.legislation.gov.uk/nisr/2026/146",
    )

    def formula(person, period, parameters):
        return disregarded_capital(person, period, parameters, True)
