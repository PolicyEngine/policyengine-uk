from policyengine_uk.model_api import *


class employment_benefits(Variable):
    value_type = float
    entity = Person
    label = "Employment benefits"
    documentation = (
        "Statutory payments that employers pay and that are taxable social "
        "security income: ITEPA 2003 s.660(1) Table A lists statutory "
        "paternity, adoption, maternity, shared parental, parental bereavement, "
        "neonatal care and sick pay, and s.658(5) charges the whole amount. "
        "The model adds them to taxable employment income; both are "
        "non-savings income, so the tax is the same."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 660(1), Table A",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/660",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 658(5)",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/658",
        ),
    ]

    adds = [
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "statutory_paternity_pay",
        "statutory_adoption_pay",
        "statutory_shared_parental_pay",
        "statutory_parental_bereavement_pay",
        "statutory_neonatal_care_pay",
    ]
