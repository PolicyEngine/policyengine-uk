from policyengine_uk.model_api import *

# The amounts each payment the charge recovers can take
# (winter_heating_payment_amount).
AMOUNTS = [
    "lower",
    "higher",
    "lower_shared",
    "higher_shared_with_under_80",
    "higher_shared_with_80_or_over",
]


class winter_fuel_payment_charge_ceiling(Variable):
    value_type = float
    entity = Person
    label = "Most winter fuel payment charge whatever benefits are received"
    documentation = (
        "The most the winter fuel payment charge (winter_fuel_payment_charge) "
        "could be for the person, whoever in their household receives which "
        "benefits: the largest amount of each payment whose age and residence "
        "conditions they meet, when the charge has effect and their total "
        "income exceeds the threshold, and nothing otherwise. Whether they "
        "are entitled to a payment beyond those conditions, which amount it "
        "is, and whether a relevant benefit exempts them all turn on benefit "
        "receipt, which this leaves out, so the charge is never more than "
        "this. It lets the property allowance election "
        "(uses_property_allowance) compare tax before the charge wherever "
        "the charge cannot change the choice, without working out benefits "
        "on both routes."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2003/1/section/681I",
        "https://www.legislation.gov.uk/uksi/2025/969/regulation/2",
        "https://www.legislation.gov.uk/ssi/2024/351/regulation/10",
    )

    def formula(person, period, parameters):
        charge = parameters(period).gov.hmrc.income_tax.charges.winter_fuel_payment
        wfp = parameters(period).gov.dwp.winter_fuel_payment
        pawhp = parameters(period).gov.social_security_scotland.pawhp
        country = person.household("country", period).decode_to_str()
        # Either age the payments test, in any year
        # (winter_fuel_payment_eligible, pawhp_eligible).
        pension_age = person("is_SP_age", period) | person(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        meets_wfp_conditions = np.isin(country, wfp.eligibility.countries) & (
            pension_age | (not wfp.eligibility.state_pension_age_requirement)
        )
        meets_pawhp_conditions = (
            pawhp.active
            & (country == "SCOTLAND")
            & (pension_age | (not pawhp.eligibility.state_pension_age_requirement))
        )
        most_payment = meets_wfp_conditions * max(
            wfp.amount[amount] for amount in AMOUNTS
        ) + meets_pawhp_conditions * max(pawhp.amount[amount] for amount in AMOUNTS)
        over_threshold = person("total_income", period) > charge.income_threshold
        return charge.in_effect * most_payment * over_threshold
