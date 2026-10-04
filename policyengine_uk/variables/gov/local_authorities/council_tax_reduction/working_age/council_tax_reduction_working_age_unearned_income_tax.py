from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._earnings import (
    working_age_unearned_income_tax,
)


class council_tax_reduction_working_age_unearned_income_tax(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction tax on counted unearned income"
    documentation = (
        "Income tax of the claimant and partner on the taxable unearned "
        "income the working-age schemes count (pensions, State Pension and "
        "taxable benefits): their non-savings income tax less the tax on their "
        "earnings, shared pro rata with property income. Wales disregards it "
        "from unearned income (WSI 2013/3029 Sch 9 para 4); Scotland counts "
        "unearned income gross (SSI 2021/249 reg 57)."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/4"

    def formula(benunit, period, parameters):
        person = benunit.members
        tax = working_age_unearned_income_tax(person, period)
        return benunit.sum(working_age_applicant_or_partner(person, period) * tax)
