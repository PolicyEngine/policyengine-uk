from policyengine_uk.model_api import *


class benefits_in_kind(Variable):
    value_type = float
    entity = Person
    label = "Taxable benefits in kind"
    documentation = (
        "Benefits the person's employment provides that the benefits code "
        "(ITEPA 2003 s. 63) treats as earnings: the company car and car "
        "fuel benefits. Income tax charges them through "
        "taxable_employment_income, and employers pay Class 1A NICs on them. "
        "They are not earnings for Class 1 NICs, nor for the earnings tests "
        "of Universal Credit (UC Regulations 2013 reg. 55(2)(a)), Housing "
        "Benefit (HB Regulations 2006 reg. 35(2)(a)) and Council Tax "
        "Reduction, so they are kept out of employment_income and "
        "employment_benefits; those tests do deduct the income tax on them. "
        "Student loan repayments and the Plan 2 interest rate leave them "
        "out too (SI 2009/470 regs. 29(4)(e) and 41). Other benefits in kind "
        "and vans are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 63 (the benefits code)",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/63",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 55(2)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Housing Benefit Regulations 2006 reg. 35(2)(a)",
            href="https://www.legislation.gov.uk/uksi/2006/213/regulation/35",
        ),
    ]
    adds = [
        "company_car_benefit",
        "car_fuel_benefit",
    ]
