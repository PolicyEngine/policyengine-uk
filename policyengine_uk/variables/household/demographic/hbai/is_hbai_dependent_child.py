from policyengine_uk.model_api import *


class is_hbai_dependent_child(Variable):
    """Dependent child as defined for Households Below Average Income (HBAI).

    HBAI (and the Family Resources Survey, whose benefit units it uses)
    counts a person as a dependent child if they are under 16, or aged 16
    to 19 and not married, in a civil partnership or living with a partner,
    living with parents or a responsible adult, and in full-time
    non-advanced education or unwaged government training.

    Datasets built from the FRS should supply this directly: it is exactly
    the FRS child-table record. The formula is a calculator fallback that
    infers the definition from benefit-unit structure:

    - everyone under 16 is a dependent child;
    - a 16- or 17-year-old who is neither the benefit-unit head nor an
      identified parent is treated as a dependent child. This keeps the
      previous age-18 treatment: the FRS puts non-dependent 16- and
      17-year-olds in their own benefit unit, so a non-head in that age
      group is normally an FRS dependent child, whatever the education
      inputs say;
    - an 18- or 19-year-old who is neither the head nor an identified parent
      is a dependent child only if they are in non-advanced education or
      approved training and the benefit unit contains an identified parent
      (`is_parent`). Without an identified parent the model cannot tell a
      dependant from a partner, so it keeps treating them as an adult.

    This is a statistical definition. Benefit and tax rules use each
    programme's own legal definition of a child.
    """

    value_type = bool
    entity = Person
    label = "Dependent child (HBAI definition)"
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#child"

    def formula(person, period, parameters):
        p = parameters(period).household.demographic.hbai.dependent_child
        age = person("age", period)
        is_parent = person("is_parent", period)
        lives_as_dependant = ~person("is_benunit_head", period) & ~is_parent
        in_education_or_training = person(
            "is_in_non_advanced_education", period
        ) | person("is_in_approved_training", period)
        lives_with_identified_parent = person.benunit.any(is_parent)
        under_child_age = age < p.age_limit
        under_18_dependant = lives_as_dependant & person("age_under_18", period)
        young_person = (
            lives_as_dependant
            & (age < p.young_person_age_limit)
            & in_education_or_training
            & lives_with_identified_parent
        )
        return under_child_age | under_18_dependant | young_person
