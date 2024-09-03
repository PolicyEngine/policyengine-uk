from policyengine_uk.model_api import *


class uc_is_child_born_before_child_limit(Variable):
    value_type = bool
    entity = Person
    label = "Born before Universal Credit child limit"
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.child.limit
        start_year = p.start_year
        birth_year = person("birth_year", period)
        if (
            person.simulation.dataset is not None
            and "frs" in person.simulation.dataset.name
        ):
            # FRS data is based on 2019 populations, so we should add (year - 2019) to the start year to account for
            # the time-fixed nature of the child limit. This should probably be revisited for a more robust solution.
            birth_year = birth_year + (period.start.year - 10)
        born_before_limit = birth_year < start_year
        return person("is_child", period) & born_before_limit
