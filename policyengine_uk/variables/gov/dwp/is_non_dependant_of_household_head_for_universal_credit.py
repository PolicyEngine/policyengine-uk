from policyengine_uk.model_api import *


class is_non_dependant_of_household_head_for_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "Non-dependant of the families liable for the household's rent (Universal Credit)"
    documentation = (
        "The Universal Credit reading of is_non_dependant_of_household_head. "
        "Under Sch 4 para 9(2)(g), DWP leaves out of the renter's "
        "non-dependants a child or qualifying young person for whom no one in "
        "the renter's extended benefit unit is responsible. The model makes "
        "the claimant and partner of a benefit unit responsible for its "
        "children and qualifying young people, so the formula leaves out a "
        "child or qualifying young person whose claimant and partner are not "
        "the renter's non-dependants, such as a boarder's or lodger's child, "
        "whose parent pays the householder (para 9(2)(d)). It also leaves out "
        "one for whom the model makes no one responsible, such as a child a "
        "local authority looks after "
        "(is_child_or_qualifying_young_person_for_universal_credit). The "
        "child of a non-dependant stays a non-dependant. Housing Benefit and "
        "council tax reduction define a non-dependant in their own words, and "
        "their rules read is_non_dependant_of_household_head."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9"

    def formula(person, period, parameters):
        non_dependant = person("is_non_dependant_of_household_head", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        # UC Regs 2013 Sch 4 para 9(2)(g): "a child or qualifying young person
        # for whom no-one in the renter's extended benefit unit is
        # responsible". In the model, the claimant and partner of a benefit
        # unit are nobody's child or qualifying young person.
        child_or_qualifying_young_person = ~claimant_or_partner & (
            person("is_child_for_universal_credit", period)
            | person("is_qualifying_young_person_for_universal_credit", period)
        )
        # The model makes the claimant and partner of the person's benefit
        # unit responsible for them, unless it makes no one responsible, as
        # for a child a local authority looks after. That claimant or partner
        # belongs to the renter's extended benefit unit when they are a
        # non-dependant (para 9(1)(c)); a boarder or lodger never does (para
        # 9(2)(d)).
        responsible_adult_is_non_dependant = person.benunit.any(
            claimant_or_partner & non_dependant
        )
        someone_in_unit_responsible = (
            person("is_child_or_qualifying_young_person_for_universal_credit", period)
            & responsible_adult_is_non_dependant
        )
        no_one_in_unit_responsible = (
            child_or_qualifying_young_person & ~someone_in_unit_responsible
        )
        return non_dependant & ~no_one_in_unit_responsible
