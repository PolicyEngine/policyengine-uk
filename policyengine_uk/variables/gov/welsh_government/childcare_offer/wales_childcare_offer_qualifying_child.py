from policyengine_uk.model_api import *


class wales_childcare_offer_qualifying_child(Variable):
    value_type = bool
    entity = Person
    label = "qualifying child for the Childcare Offer for Wales"
    documentation = (
        "A child aged 3 or 4 living in Wales, for whom eligible parents can "
        "take up the childcare element of the Childcare Offer for Wales "
        "(guidance paras 48, 49 and 54). Funded childcare starts the term "
        "after the third birthday and ends when the child becomes eligible "
        "for a full-time school place, usually the September after the "
        "fourth birthday; the annual model counts every child aged 3 or 4."
    )
    definition_period = YEAR
    reference = "https://www.gov.wales/sites/default/files/publications/2026-04/childcare-offer-for-wales-guidance-for-local-authorities-april-2026-english_0.pdf"

    def formula(person, period, parameters):
        p = parameters(period).gov.welsh_government.childcare_offer
        if not p.in_effect:
            return np.zeros(person.count, dtype=bool)
        country = person.household("country", period)
        in_wales = country == country.possible_values.WALES
        age = person("age", period)
        return in_wales & (age >= p.age.min) & (age < p.age.max)
