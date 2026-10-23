from policyengine_uk.model_api import *


class pension_annual_allowance_chargeable_amount(Variable):
    value_type = float
    entity = Person
    label = "Chargeable amount for the pension annual allowance charge"
    documentation = (
        "The default chargeable amount (FA 2004 s. 227ZA(3)): the total pension "
        "input amount less the annual allowance, which unused annual allowance "
        "brought forward increases (s. 228A(2)). Nil if the input amount is "
        "within that allowance."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2004 s. 227ZA",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/227ZA",
        ),
        dict(
            title="Finance Act 2004 s. 228A",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/228A",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        pension_input_amount = person(
            "pension_contributions_for_annual_allowance", period
        )
        annual_allowance = person("pension_annual_allowance", period) + max_(
            0, person("unused_pension_annual_allowance", period)
        )
        return max_(0, pension_input_amount - annual_allowance)
