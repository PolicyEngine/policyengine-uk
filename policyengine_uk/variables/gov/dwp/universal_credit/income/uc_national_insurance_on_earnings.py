from policyengine_uk.model_api import *


class uc_national_insurance_on_earnings(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit deduction for National Insurance on the person's earnings"
    documentation = (
        "Primary Class 1 contributions on the person's employment and Class 2 "
        "and Class 4 contributions on their trade, which Universal Credit "
        "deducts from their earned income. Voluntary Class 3 contributions "
        "are not in respect of an employment or trade, so are not deducted."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 55(5)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2), step 3",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
    ]
    adds = [
        "ni_class_1_employee",
        "ni_class_2",
        "ni_class_4",
    ]
