from policyengine_uk.model_api import *


class adult_dependants_grant_adult_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Has an eligible dependant adult for Adult Dependants' Grant"
    documentation = (
        "Whether the student has a dependant adult who can qualify them for Adult Dependants' Grant. "
        "By default, the model treats co-resident couple students aged 25 or over as satisfying the partner rule, "
        "and provides an explicit input path for other adult dependants or under-25 married/civil-partner cases."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.adult_dependants_grant
        is_couple = person.benunit("is_couple", period)
        age = person("age", period)
        has_other_adult_dependant = person(
            "adult_dependants_grant_has_other_adult_dependant", period
        )
        other_adult_income = person("adult_dependants_grant_other_adult_income", period)

        partner_path = is_couple & (age >= 25)
        other_adult_path = has_other_adult_dependant & (
            other_adult_income <= p.other_adult_income_limit
        )

        return partner_path | other_adult_path
