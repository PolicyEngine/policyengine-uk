from openfisca_uk.model_api import *


class CB_HITC(Variable):
    value_type = float
    entity = Person
    label = "Child Benefit High-Income Tax Charge"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2003/1/part/10/chapter/8"
    unit = "currency-GBP"

    def formula(person, period, parameters):
        CB_received = person.benunit("child_benefit", period)
        CB_HITC = parameters(period).tax.income_tax.charges.CB_HITC
        percentage = (
            amount_over(
                person("adjusted_net_income", period),
                CB_HITC.phase_out_start,
            )
            # HITC is specified as a percent of Child Benefit recollected for every £1,000 over the phase-out threshold.
            / 1_000
            * CB_HITC.phase_out_rate
        )
        is_higher_earner = person("is_higher_earner", period)
        return (min_(percentage, 1) * CB_received) * is_higher_earner
