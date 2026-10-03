from policyengine_uk.model_api import *


class ni_class_1_income(Variable):
    label = "ni_class_1_income"
    documentation = (
        "Income subject to NI Class 1 contributions: employment income and, "
        "under SSCBA 1992 s.4(1)(a), the statutory payments treated as "
        "remuneration from the employment (sick, maternity, paternity, "
        "adoption, shared parental, parental bereavement and neonatal care "
        "pay). Employee pension contributions are not deducted."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "employment_income",
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "statutory_paternity_pay",
        "statutory_adoption_pay",
        "statutory_shared_parental_pay",
        "statutory_parental_bereavement_pay",
        "statutory_neonatal_care_pay",
    ]
    reference = [
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 3",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/3",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 4(1)(a)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/4",
        ),
        dict(
            title="Social Security Contributions and Benefits (Northern Ireland) Act 1992 s. 4(1)(a)",
            href="https://www.legislation.gov.uk/ukpga/1992/7/section/4",
        ),
    ]
