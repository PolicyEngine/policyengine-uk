from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    national_insurance_on_threshold,
)


class uc_minimum_income_floor_national_insurance(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor deduction for National Insurance"
    documentation = (
        "The amount for National Insurance deducted from the person's gross "
        "individual threshold to give their net minimum income floor. The "
        "regulations leave it to the Secretary of State. The model takes the "
        "contributions the person would pay if the threshold were their only "
        "earnings: Class 2 and Class 4 on self-employed profits of that "
        "amount, as in DWP's figures, or primary Class 1 on pay of that "
        "amount where the parameter selects it."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 62(4)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 ss. 8, 11 and 15",
            href="https://www.legislation.gov.uk/ukpga/1992/4/part/I",
        ),
    ]

    def formula(person, period, parameters):
        return national_insurance_on_threshold(
            person,
            period,
            parameters,
            person("uc_minimum_income_floor_gross", period),
        )
