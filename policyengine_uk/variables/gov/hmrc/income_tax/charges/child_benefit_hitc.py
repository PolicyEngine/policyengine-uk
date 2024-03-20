from policyengine_uk.model_api import *


class CB_HITC(Variable):
    value_type = float
    entity = Person
    label = "Child Benefit High-Income Tax Charge"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2003/1/part/10/chapter/8"
    unit = GBP
    defined_for = "is_higher_earner"

    def formula(person, period, parameters):
        CB_received = person.benunit("child_benefit", period)
        CB_HITC = parameters(period).gov.hmrc.income_tax.charges.CB_HITC
        percentage = (
            max_(
                person("adjusted_net_income", period)
                - CB_HITC.phase_out_start,
                0,
            )
            # HITC is specified as a percent of Child Benefit recollected for
            # every £1,000 over the phase-out threshold.
            / 1_000
            * CB_HITC.phase_out_rate
        )
        return min_(percentage, 1) * CB_received
