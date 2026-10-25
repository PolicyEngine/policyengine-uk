from policyengine_uk.model_api import *


class lifetime_isa_withdrawal_charge(Variable):
    value_type = float
    entity = Person
    label = "Lifetime ISA withdrawal charge"
    documentation = "Charge deducted from non-exempt gross Lifetime ISA withdrawals. The model records this capital payment as government revenue, outside household current-income taxes; a supplied balance is not automatically updated. Annual rates use the model's fiscal-year parameter sampling."
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.isa.lifetime
        if not p.in_effect:
            return 0
        gross = max_(person("lifetime_isa_withdrawals", period), 0)
        price = person.household("main_residential_property_purchased", period)
        qualifying_home = (
            person("lifetime_isa_first_time_buyer", period)
            & person.household("main_residential_property_purchased_is_in_uk", period)
            & person.household(
                "main_residential_property_purchased_with_mortgage", period
            )
            & (
                person("lifetime_isa_months_since_first_payment", period)
                >= p.minimum_holding_period
            )
            & (price > 0)
            & (price <= p.property_price_cap)
        )
        home_payment = min_(
            max_(person("lifetime_isa_withdrawals_towards_first_home", period), 0),
            min_(gross, max_(price, 0)),
        )
        exempt = (person("age", period) >= p.charge_free_age) | person(
            "lifetime_isa_terminally_ill", period
        )
        chargeable = max_(gross - where(qualifying_home, home_payment, 0), 0)
        return where(exempt, 0, chargeable * p.withdrawal_charge)
