from policyengine_uk.model_api import *


class council_tax_reduction_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible person for CTR non-dependent deduction"
    documentation = (
        "A non-dependant aged 18 or over: an adult outside the claimant's "
        "family who is not liable for rent, or a member of a claiming "
        "family's benefit unit who is not its claimant, partner or a child or "
        "young person (see is_benefit_unit_non_dependant_for_legacy_benefits). "
        "Someone jointly and severally liable for the council tax with the "
        "claimant (a joint tenant or other sharer of the rent) and a boarder "
        "or lodger, with their family, is not a non-dependant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/9",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/3",
    )

    def formula(person, period, parameters):
        # SI 2012/2885 reg 9(2)(a), (c)-(e) and the Welsh and Scottish
        # equivalents; deductions are for non-dependants aged 18 or over.
        other_family = ~person.benunit(
            "benunit_contains_household_head", period
        ) & ~person.benunit("benunit_is_rent_liable", period)
        # A member of a claiming family's own benefit unit who is not in its
        # claimant's family. A boarder's or lodger's family is one commercial
        # arrangement, so its members are no one's non-dependants.
        own_family = person(
            "is_benefit_unit_non_dependant_for_legacy_benefits", period
        ) & person.benunit("council_tax_reduction_claimant_benunit", period)
        return (person("age", period) >= 18) & (other_family | own_family)
