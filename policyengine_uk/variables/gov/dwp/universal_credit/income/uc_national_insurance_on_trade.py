from policyengine_uk.model_api import *


class uc_national_insurance_on_trade(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit deduction for National Insurance on the person's trade"
    documentation = (
        "Class 2 and Class 4 contributions, paid in respect of the person's "
        "trade, which reg. 57(2) step 3 deducts inside the self-employed "
        "earnings calculation. The rest of uc_national_insurance_on_earnings "
        "(primary Class 1) is in respect of the employment (reg. 55(5)(b))."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Universal Credit Regulations 2013 reg. 57(2), step 3",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
    )

    def formula(person, period, parameters):
        trade = add(person, period, ["ni_class_2", "ni_class_4"])
        # Never more than the NI on earnings in use, which can be an input:
        # the rest of that figure is in respect of the employment.
        return min_(trade, person("uc_national_insurance_on_earnings", period))
