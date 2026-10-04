from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._earnings import (
    working_age_earnings,
)


class council_tax_reduction_working_age_employed_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction net employed earnings"
    documentation = (
        "The employed part of the claimant's and partner's net earnings: "
        "employment income and statutory sick, maternity and paternity pay, "
        "sharing each person's deductions pro rata with their self-employed "
        "earnings. Scotland's additional £17.10 earnings disregard turns on "
        "employed earnings from April 2022."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ssi/2021/249/schedule/3"

    def formula(benunit, period, parameters):
        person = benunit.members
        _, employed = working_age_earnings(person, period)
        return benunit.sum(working_age_applicant_or_partner(person, period) * employed)
