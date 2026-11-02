from policyengine_uk.model_api import *


class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported income from the State Pension"
    documentation = (
        "The State Pension a survey reports, as an annual amount: the weekly "
        "amount times 52. basic_state_pension, new_state_pension and "
        "additional_state_pension divide it by 52 and split the weekly amount "
        "at the data year's full rate for the type the person has in the year "
        "being calculated, so a dataset must annualise weekly amounts at 52 "
        "weeks. At 365.25 / 7, a full-rate pensioner reads 0.34% above the "
        "full rate and gets the excess as additional State Pension or a "
        "protected payment."
    )
    definition_period = YEAR
    unit = GBP

    def formula_2022(person, period, parameters):
        return person("state_pension_reported", period.last_year)
