from policyengine_uk.model_api import *


class employment_benefits(Variable):
    value_type = float
    entity = Person
    label = "Employment benefits"
    documentation = (
        "Statutory sick, maternity and paternity pay. ITEPA 2003 s. 660 "
        "Table A lists each as a taxable social security benefit; employers "
        "pay them through payroll, and taxable_employment_income taxes them "
        "with wages. Table A also lists statutory adoption, shared parental, "
        "parental bereavement and neonatal care pay; the model has no "
        "variables for those."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Earnings and Pensions) Act 2003, s. 660, Table A",
        href="https://www.legislation.gov.uk/ukpga/2003/1/section/660",
    )

    adds = [
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "statutory_paternity_pay",
    ]
