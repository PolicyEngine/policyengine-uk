from policyengine_uk.model_api import *


class plan_4_interest_rate(Variable):
    value_type = float
    entity = Person
    label = "Plan 4 student loan interest rate"
    documentation = (
        "Interest rate for Plan 4 student loans (Scotland). "
        "Set at the lower of RPI or Bank of England base rate + 1%. "
        "Same calculation as Plan 1, defined via amendments to SI 2009/470."
    )
    definition_period = YEAR
    unit = "/1"
    reference = [
        "https://www.legislation.gov.uk/uksi/2009/470/regulation/21",
        "https://www.legislation.gov.uk/uksi/2022/1335",  # Plan 4 amendments
    ]

    def formula(person, period, parameters):
        # Plan 4 uses identical interest rate calculation as Plan 1
        return person("plan_1_interest_rate", period)
