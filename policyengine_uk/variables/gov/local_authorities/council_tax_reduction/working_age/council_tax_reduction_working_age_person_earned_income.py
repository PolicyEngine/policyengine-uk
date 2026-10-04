from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._earnings import (
    working_age_earnings,
)


class council_tax_reduction_working_age_person_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Working-age council tax reduction net earned income (person)"
    documentation = (
        "A claimant's or partner's annual net earnings for a working-age "
        "council tax reduction claim in Scotland or Wales, before earnings "
        "disregards. Only income tax and National Insurance in respect of the "
        "employment or trade are deducted (not tax on pensions, benefits, "
        "property, savings or dividends, nor voluntary Class 3 "
        "contributions). With Universal Credit, Wales uses the Universal "
        "Credit earned income the award is based on, and Scotland adds "
        "statutory sick, maternity and paternity pay to it; otherwise half of "
        "pension contributions are deducted. Children's and other members' "
        "earnings do not count."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/49",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/50",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/15",
    )

    def formula(person, period, parameters):
        net, _ = working_age_earnings(person, period)
        return working_age_applicant_or_partner(person, period) * net
