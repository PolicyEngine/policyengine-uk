from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class has_non_dependant_for_council_tax_reduction_severe_disability_premium(Variable):
    value_type = bool
    entity = BenUnit
    label = "Has a non-dependant who blocks the CTR severe disability premium"
    documentation = (
        "Uses the applicant family's Council Tax Reduction young-person definition "
        "for non-looked-after members of its own benefit unit in Scotland's "
        "working-age scheme. The applicant's own pensioner status and the dated "
        "young-person parameter select that scheme. All other schemes retain "
        "the shared Housing Benefit/Income Support test. Blind residents and "
        "qualifying-benefit recipients remain disregarded. Looked-after members "
        "retain the exact existing Child Benefit family classification, and "
        "other benefit units retain the existing treatment. Reg 8(2)(b), subject "
        "to reg 8(3), also excludes some young people outside the applicant's "
        "responsibility; the model lacks complete tenancy and responsibility "
        "relations for those looked-after and other-benefit-unit cases. They "
        "remain outside this partial correction. Other limitations of "
        "has_non_dependant_for_severe_disability_premium also remain."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/6",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/8",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/13",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.disability_premia
        person = benunit.members
        counted = (
            (person("age", period) >= p.severe_non_dependant_age)
            & ~person("receives_severe_disability_premium_qualifying_benefit", period)
            & ~person("is_blind", period)
        )
        child_or_young_person = where(
            person("is_looked_after_by_local_authority", period),
            person("is_child_or_qualifying_young_person_for_child_benefit", period),
            person("is_child_or_young_person_for_council_tax_reduction", period),
        )
        family = person("is_claimant_or_partner", period) | child_or_young_person
        in_household = benunit.max(person.household.sum(counted))
        non_dependant = in_household > benunit.sum(counted & family)
        scotland = parameters(
            period
        ).gov.local_authorities.scotland.council_tax_reduction.working_age
        scottish_working_age = (
            (benunit.household("country", period) == Country.SCOTLAND)
            & ~benunit("council_tax_reduction_pensioner", period)
            & scotland.young_person_follows_universal_credit
        )
        return where(
            scottish_working_age,
            non_dependant,
            benunit("has_non_dependant_for_severe_disability_premium", period),
        )
