from policyengine_uk.model_api import *


class pension_annual_allowance_taxable_lump_sum_death_benefits(Variable):
    value_type = float
    entity = Person
    label = "Taxable lump-sum death benefits excluded from annual allowance incomes"
    documentation = (
        "The taxable pension lump-sum death benefits already included in "
        "net_income, excluded by FA 2004 s. 228ZA(4)(e) and (5)(d). "
        "Supply the taxable benefit separately as income as well as here; "
        "this input only removes it from the taper income tests. "
        "Defaults to zero because survey data do not identify these benefits."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2004/12/section/228ZA"
