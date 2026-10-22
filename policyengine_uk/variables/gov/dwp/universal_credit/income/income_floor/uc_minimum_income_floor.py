from policyengine_uk.model_api import *


class uc_minimum_income_floor(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor"
    documentation = (
        "The person's individual threshold converted to a net amount: the "
        "gross threshold less the amounts for income tax and National "
        "Insurance. A claimant to whom the floor applies is treated as having "
        "this much earned income, after deductions, when their own is lower."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 62(4)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
        dict(
            title="Advice for Decision Making, chapter H4, H4078-H4079",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]

    def formula(person, period, parameters):
        gross = person("uc_minimum_income_floor_gross", period)
        deductions = add(
            person,
            period,
            [
                "uc_minimum_income_floor_income_tax",
                "uc_minimum_income_floor_national_insurance",
            ],
        )
        return max_(0, gross - deductions)
