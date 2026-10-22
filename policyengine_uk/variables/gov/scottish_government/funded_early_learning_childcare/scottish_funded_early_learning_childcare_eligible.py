from policyengine_uk.model_api import *


class scottish_funded_early_learning_childcare_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for Scottish funded early learning and childcare"
    documentation = (
        "Whether this person is eligible for the universal age-based strand of "
        "Scotland's funded early learning and childcare (ELC) provision. Does "
        "not yet model the eligible-two-year-old strand (vulnerable / low-income "
        "children aged 2 also qualify under Part 2 of the 2014 Order). "
        "Three-year-olds qualify only once they have reached the statutory "
        "start date. A child who has started primary 1 no longer qualifies "
        "(early_years_child_in_school)."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/asp/2014/8/section/47",
        "https://www.legislation.gov.uk/asp/2014/8/section/48",
        "https://www.gov.scot/publications/early-learning-childcare-statutory-guidance-july-2021/pages/8/",
    ]

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        in_scotland = country == countries.SCOTLAND

        age = person("age", period)
        p = parameters(period).gov.scottish_government.funded_early_learning_childcare
        start_date_reached = person(
            "scottish_funded_early_learning_childcare_start_date_reached",
            period,
        )
        eligible_three_year_old = (
            (age >= p.age.min) & (age < p.age.min + 1) & start_date_reached
        )
        eligible_older_child = (age >= p.age.min + 1) & (age < p.age.max)

        # Children and Young People (Scotland) Act 2014 s.47(2)(b): an
        # eligible pre-school child "has not commenced attendance at a
        # primary school (other than at a nursery class in such a school)".
        in_school = person("early_years_child_in_school", period)

        return (
            in_scotland & (eligible_three_year_old | eligible_older_child) & ~in_school
        )
