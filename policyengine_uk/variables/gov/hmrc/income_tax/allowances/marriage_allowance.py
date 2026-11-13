from policyengine_uk.model_api import *


class would_claim_marriage_allowance(Variable):
    label = "Would claim Marriage Allowance"
    documentation = (
        "Whether this person would claim Marriage Allowance if eligible. "
        "Generated stochastically in the dataset using take-up rates."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True


class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance"
    documentation = (
        "The amount of personal allowance transferred to this person. It does "
        "not reduce their taxable income: marriage_allowance_tax_reduction "
        "gives them a tax reduction of the appropriate percentage of it at "
        "Step 6 (ITA 2007 s. 55B(1))."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/part/3/chapter/3A"
    unit = GBP

    def formula(person, period, parameters):
        return person("meets_marriage_allowance_income_conditions", period) * (
            person("marriage_allowance_if_income_conditions_met", period)
        )
