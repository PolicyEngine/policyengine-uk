from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    income_tax_on_threshold,
)


class uc_minimum_income_floor_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor deduction for income tax"
    documentation = (
        "The amount for income tax deducted from the person's gross "
        "individual threshold to give their net minimum income floor. The "
        "regulations leave it to the Secretary of State; the model takes the "
        "income tax the person would pay if the threshold were their only "
        "income: the threshold less the standard personal allowance, at the "
        "person's own rest-of-UK or Scottish rates."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 62(4)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
        dict(
            title="Advice for Decision Making, chapter H4, H4078-H4079",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]

    def formula(person, period, parameters):
        return income_tax_on_threshold(
            person,
            period,
            parameters,
            person("uc_minimum_income_floor_gross", period),
        )
