from policyengine_uk.model_api import *


class is_uc_non_dependant_of_household_head(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit non-dependant of the household's renter"
    documentation = (
        "Whether this person is a non-dependant in the Universal Credit "
        "extended benefit unit of the household's renter. The formula starts "
        "from is_non_dependant_of_household_head and leaves out, under UC "
        "Regs 2013 Sch 4 para 9(2)(g), a child or qualifying young person "
        "for whom no one in the renter's extended benefit unit is "
        "responsible. The model takes the claimant and partner of a child's "
        "own benefit unit as the people responsible for them. Under para "
        "9(2)(d), DWP leaves a boarder or lodger out of the extended benefit "
        "unit, and the model leaves out their partner too "
        "(pays_rent_to_householder). The formula therefore leaves out their "
        "children and qualifying young people, who supply no bedroom under "
        "paras 8 and 10. A child whose parent pays nothing stays a "
        "non-dependant, because the parent belongs to the extended benefit "
        "unit. Where a child's benefit unit has no claimant or partner, the "
        "model cannot tell who is responsible for them and keeps them a "
        "non-dependant. The Housing Benefit and Council Tax Reduction "
        "formulas read is_non_dependant_of_household_head, which follows "
        "their own definitions."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/8",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10",
    )

    def formula(person, period, parameters):
        non_dependant = person("is_non_dependant_of_household_head", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        # UC Regs 2013 Sch 4 para 9(2)(g): "a child or qualifying young
        # person for whom no-one in the renter's extended benefit unit is
        # responsible". The model forms each benefit unit around its
        # claimant and partner, so neither counts as anyone's child.
        child_or_qualifying_young_person = (
            person("is_child_for_universal_credit", period)
            | person("is_qualifying_young_person_for_universal_credit", period)
        ) & ~claimant_or_partner
        # The model takes the claimant or partner of the child's own benefit
        # unit as responsible for them. They belong to the renter's extended
        # benefit unit only as non-dependants (para 9(1)(c)); a boarder or
        # lodger liable on a commercial basis does not (para 9(2)(d)).
        responsible = person.benunit.any(claimant_or_partner)
        responsible_in_extended_unit = person.benunit.any(
            claimant_or_partner & non_dependant
        )
        no_one_responsible = (
            child_or_qualifying_young_person
            & responsible
            & ~responsible_in_extended_unit
        )
        return non_dependant & ~no_one_responsible
