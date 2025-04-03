from policyengine_uk.model_api import *


class is_parent(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a parent in their benefit unit"
    definition_period = YEAR

    def formula(person, period, parameters):
        benunit = person.benunit
        age = person("age", period)
        family_type = benunit("family_type", period)

        # Find two oldest members
        benunit_ages = benunit.members("age", period)
        adult_index = person("adult_index", period)

        # Get family types enum
        family_types = family_type.possible_values

        # For lone parents (FamilyType.LONE_PARENT), only the eldest is parent
        is_lone_parent = (family_type == family_types.LONE_PARENT) & (
            adult_index == 1
        )

        # For couples with children (FamilyType.COUPLE_WITH_CHILDREN), two eldest are parents
        is_couple_parent = (
            family_type == family_types.COUPLE_WITH_CHILDREN
        ) & ((adult_index == 1) | (adult_index == 2))

        return is_lone_parent | is_couple_parent
