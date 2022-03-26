from openfisca_uk.model_api import *


@uprated(by="september_cpi")
class student_loans(Variable):
    value_type = float
    entity = Person
    label = "Student loans"
    definition_period = YEAR
    unit = "currency-GBP"


@uprated(by="september_cpi")
class adult_ema(Variable):
    label = "Adult EMA"
    documentation = "Educational Maintenance Allowance for adults"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


@uprated(by="september_cpi")
class child_ema(Variable):
    label = "Child EMA"
    documentation = "Educational Maintenance Allowance for children"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


@uprated(by="september_cpi")
class access_fund(Variable):
    label = "Access Fund"
    documentation = "Access Fund for educational assistance"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


@uprated(by="september_cpi")
class education_grants(Variable):
    label = "Education grants"
    documentation = "Grants for education"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class student_payments(Variable):
    value_type = float
    entity = Person
    label = "Student payments"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        EDUCATION_BENEFITS = [
            "adult_ema",
            "child_ema",
            "access_fund",
            "education_grants",
        ]
        return add(person, period, EDUCATION_BENEFITS)
