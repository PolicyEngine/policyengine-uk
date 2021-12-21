from openfisca_uk.model_api import *


class CB_HITC(Variable):
    value_type = float
    entity = Person
    label = "Child Benefit High-Income Tax Charge"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2003/1/part/10/chapter/8"

    def formula(person, period, parameters):
        CB_received = person.benunit("child_benefit", period)
        CB_HITC = parameters(period).tax.income_tax.charges.CB_HITC
        percentage = (
            amount_over(
                person("adjusted_net_income", period),
                CB_HITC.phase_out_start,
            )
            / 1_000
            * CB_HITC.phase_out_rate
        )
        return (percentage * CB_received) * person("is_higher_earner", period)
