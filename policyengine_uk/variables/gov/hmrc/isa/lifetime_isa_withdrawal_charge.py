from policyengine_uk.model_api import *


class lifetime_isa_withdrawal_charge(Variable):
    value_type = float
    entity = Person
    label = "Lifetime ISA withdrawal charge"
    documentation = "Charge deducted from non-exempt gross Lifetime ISA withdrawals. From 29 October 2026, the part paid towards a first home that meets every first-time purchase condition except the property price cap pays the reduced above-cap charge (Schedule paragraph 6A). The annual model reads parameters on 30 April, so it applies the reduced charge from fiscal 2027-28: a 2026-27 run charges such a withdrawal made from 29 October 2026 to 5 April 2027 at the full withdrawal charge, 25% rather than 20%. The model records this capital payment as government revenue, outside household current-income taxes; a supplied balance is not automatically updated. Annual rates use the model's fiscal-year parameter sampling."
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
        # Schedule paragraph 6, apart from the price cap in 6(3).
        first_home = (
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
        )
        within_cap = price <= p.property_price_cap
        qualifying_home = first_home & within_cap
        # Paragraph 6A: a purchase that fails only the price cap pays the
        # reduced above-cap charge instead of the withdrawal charge.
        above_cap_home = first_home & ~within_cap & p.above_cap_purchase.in_effect
        home_payment = min_(
            max_(person("lifetime_isa_withdrawals_towards_first_home", period), 0),
            min_(gross, max_(price, 0)),
        )
        exempt = (person("age", period) >= p.charge_free_age) | person(
            "lifetime_isa_terminally_ill", period
        )
        above_cap_payment = where(above_cap_home, home_payment, 0)
        chargeable = max_(
            gross - where(qualifying_home, home_payment, 0) - above_cap_payment, 0
        )
        charge = (
            chargeable * p.withdrawal_charge
            + above_cap_payment * p.above_cap_purchase.withdrawal_charge
        )
        return where(exempt, 0, charge)
