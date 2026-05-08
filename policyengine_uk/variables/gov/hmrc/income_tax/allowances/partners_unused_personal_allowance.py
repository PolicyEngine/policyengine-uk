from policyengine_uk.model_api import *
from numpy import ceil


class partners_unused_personal_allowance(Variable):
    label = "Partner's unused personal allowance"
    documentation = (
        "The personal tax allowance not used by this person's partner, if they exist"
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        is_adult = person("is_adult", period)
        pa = person("unused_personal_allowance", period)
        # Subtract this person's own unused PA only if they are an adult, so
        # non-adults (whose PA isn't part of the adult-summed pool) cannot
        # produce a negative transferable amount.
        return person.benunit.sum(is_adult * pa) - is_adult * pa
