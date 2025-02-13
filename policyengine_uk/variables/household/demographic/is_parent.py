from policyengine_uk.model_api import *


class is_parent(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a parent in the benefit unit"
    definition_period = YEAR

    def formula(person, period, parameters):
        benunit = person.benunit
        age = person("age", period)
        family_type = benunit("family_type", period)

        # Find two oldest members
        benunit_ages = benunit.members("age", period)
        first_highest = benunit.max(benunit_ages)
        is_among_two_oldest = (age == first_highest) | (
            age
            == benunit.max(
                where(benunit_ages < first_highest, benunit_ages, -np.inf)
            )
        )

        # For lone parents (type 2), only eldest is parent
        is_lone_parent = (family_type == 2) & (age == first_highest)

        # For couples with children (type 3), two eldest are parents
        is_couple_parent = (family_type == 3) & is_among_two_oldest

        return is_lone_parent | is_couple_parent
