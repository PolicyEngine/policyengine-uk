from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._earnings import (
    working_age_earnings_components,
)


class council_tax_reduction_working_age_person_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Working-age council tax reduction net earned income (person)"
    documentation = (
        "A claimant's or partner's annual net earnings for a working-age "
        "council tax reduction claim in Scotland or Wales, before earnings "
        "disregards: gross earnings less pension contributions (all of them "
        "with Universal Credit, half otherwise) and the person's income tax "
        "and National Insurance, not below zero. Children's and other "
        "members' earnings do not count."
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
        gross, _, pension_deduction, tax = working_age_earnings_components(
            person, period
        )
        claimant_or_partner = working_age_applicant_or_partner(person, period)
        return claimant_or_partner * max_(0, gross - pension_deduction - tax)
