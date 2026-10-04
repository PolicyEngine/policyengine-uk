from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._earnings import (
    working_age_earnings_components,
)


class council_tax_reduction_working_age_unabsorbed_tax(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction tax not absorbed by earnings"
    documentation = (
        "Income tax and National Insurance of the claimant and partner beyond "
        "what their earnings (less pension deductions) can absorb, which is "
        "tax on unearned income. Wales disregards it from unearned income "
        "(WSI 2013/3029 Sch 9 para 4); Scotland counts unearned income gross "
        "(SSI 2021/249 reg 57)."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/wsi/2013/3029/schedule/9/paragraph/4"

    def formula(benunit, period, parameters):
        person = benunit.members
        gross, _, pension_deduction, tax = working_age_earnings_components(
            person, period
        )
        claimant_or_partner = working_age_applicant_or_partner(person, period)
        absorbed = max_(0, gross - pension_deduction)
        return benunit.sum(claimant_or_partner * max_(0, tax - absorbed))
