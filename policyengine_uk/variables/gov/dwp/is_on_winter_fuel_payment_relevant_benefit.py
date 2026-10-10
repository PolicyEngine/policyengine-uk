from policyengine_uk.model_api import *
from policyengine_uk.utils.winter_heating import is_on_relevant_benefit


class is_on_winter_fuel_payment_relevant_benefit(Variable):
    value_type = bool
    entity = Person
    label = "on a relevant benefit for the Winter Fuel Payment"
    documentation = (
        "Whether this person is on a relevant benefit for the Winter Fuel "
        "Payment. The relevant benefits are listed by period in "
        "gov.dwp.winter_fuel_payment.eligibility.relevant_benefits; for the "
        "2024 qualifying week a tax credit award of at least £26 also counts "
        "(minimum_tax_credit_award). Under SI 2000/729 and SI 2025/969 the "
        "person is on one when it is paid to them: Income Support, "
        "income-based JSA, income-related ESA and Pension Credit are paid to "
        "one member of a couple, while Universal Credit is a joint award "
        "paid to both (WRA 2012 s.1(2)(b); Universal Credit etc. (Claims and "
        "Payments) Regulations 2013 reg 47(4) and (6)). For the 2024 "
        "qualifying week a member of a couple is "
        "also on one when the other member is (SI 2024/869 reg 2(5); "
        "partner_receipt_counts). A non-dependant's relevant benefit never "
        "counts for anyone else in the household."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2000/729/regulation/2",
        "https://www.legislation.gov.uk/uksi/2024/869/regulation/2",
        "https://www.legislation.gov.uk/uksi/2025/969/regulation/1",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.winter_fuel_payment.eligibility
        return is_on_relevant_benefit(person, period, p)
