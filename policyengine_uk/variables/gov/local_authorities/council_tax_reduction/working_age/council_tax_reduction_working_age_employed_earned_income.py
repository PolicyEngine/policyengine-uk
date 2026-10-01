from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._earnings import (
    working_age_earnings_components,
)


class council_tax_reduction_working_age_employed_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction net employed earnings"
    documentation = (
        "The employed part of the claimant's and partner's net earnings: "
        "employment income and statutory sick, maternity and paternity pay, "
        "with each person's deductions shared pro rata with their "
        "self-employed earnings. Scotland's additional £17.10 earnings "
        "disregard turns on employed earnings from April 2022."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ssi/2021/249/schedule/3"

    def formula(benunit, period, parameters):
        person = benunit.members
        gross, employed_gross, _, _ = working_age_earnings_components(person, period)
        net = person("council_tax_reduction_working_age_person_earned_income", period)
        share = np.divide(
            employed_gross,
            gross,
            out=np.zeros_like(gross, dtype=float),
            where=gross > 0,
        )
        return benunit.sum(net * share)
