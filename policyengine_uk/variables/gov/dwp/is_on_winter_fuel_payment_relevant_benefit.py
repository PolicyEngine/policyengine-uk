from policyengine_uk.model_api import *
from policyengine_uk.utils.winter_heating import is_on_relevant_benefit


class is_on_winter_fuel_payment_relevant_benefit(Variable):
    value_type = bool
    entity = Person
    label = "on a relevant benefit for the Winter Fuel Payment"
    documentation = (
        "Whether a relevant benefit for the Winter Fuel Payment is paid to "
        "this person. The relevant benefits are listed by period in "
        "gov.dwp.winter_fuel_payment.eligibility.relevant_benefits; for the "
        "2024 qualifying week a tax credit award of at least £26 also counts "
        "(minimum_tax_credit_award). A couple's award covers both partners, "
        "so the claimant and the partner are on it when their benefit unit's "
        "award is positive (SI 2024/869 reg 2(5) says so expressly; under SI "
        "2000/729 and SI 2025/969 the couple receives one payment either "
        "way). Any other member of the benefit unit, such as a non-dependent "
        "adult, is on it only through their own award: their relevant benefit "
        "never counts for anyone else in the household."
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
