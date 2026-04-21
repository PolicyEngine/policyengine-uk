from policyengine_uk.model_api import *


class scottish_funded_early_learning_childcare_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for Scottish funded early learning and childcare"
    documentation = (
        "Whether this person is eligible for the universal age-based strand of "
        "Scotland's funded early learning and childcare (ELC) provision. Does "
        "not yet model the eligible-two-year-old strand (vulnerable / low-income "
        "children aged 2 also qualify under Part 2 of the 2014 Order)."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/asp/2014/8/section/48"

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        in_scotland = country == countries.SCOTLAND

        age = person("age", period)
        p = parameters(period).gov.scottish_government.funded_early_learning_childcare
        meets_age_condition = (age >= p.age.min) & (age < p.age.max)

        return in_scotland & meets_age_condition
