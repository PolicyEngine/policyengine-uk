from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim,
)


class uc_carer_element_included_for_claimant(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit carer element included in respect of this claimant"
    documentation = (
        "Whether the Universal Credit award includes the carer element in "
        "respect of this person. Only a claimant (`is_uc_assessed_claimant`, "
        "less the other member of a single claim under reg. 3(3)) "
        "who has regular and substantial caring responsibilities for a "
        "severely disabled person (`is_carer_for_benefits`) qualifies, so a "
        "child or qualifying young person who cares does not. A claimant in "
        "respect of whom the award's LCWRA element is included has only that "
        "element. The LCWRA element is one per award; where it is included "
        "(`uc_LCWRA_element` positive) and more than one claimant has limited "
        "capability for work and work-related activity, the model takes it "
        "to be included in respect of one who is not a carer if there is "
        "one, and otherwise the elder, so the other keeps the carer element. "
        "Where it is not included (an award of nil, as in the reg. 28 "
        "waiting period), a carer's limited capability does not displace the "
        "carer element. Joint claimants who both qualify have an element "
        "each unless they care for the same severely disabled person "
        "(`partners_care_for_same_severely_disabled_person`); then only one "
        "is included, which they elect or the Secretary of State decides, "
        "and the model takes the elder."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 12(2)(c)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/12",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 29(1) to (4)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/29",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 27(4)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/27",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 30",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/30",
        ),
    ]

    def formula(person, period, parameters):
        benunit = person.benunit
        age = person("age", period)
        # Reg. 29(1): "where a claimant has regular and substantial caring
        # responsibilities for a severely disabled person" (reg. 30).
        claimant = person(
            "is_uc_assessed_claimant", period
        ) & ~other_member_of_single_claim(person, period)
        carer = claimant & person("is_carer_for_benefits", period)
        limited_capability = claimant & person("uc_limited_capability_for_WRA", period)
        # Reg. 29(4): a carer with limited capability "(and, in the case of
        # joint claimants, the LCWRA element has not been included in respect
        # of the other claimant)" has "only the LCWRA element". The award has
        # one LCWRA element (reg. 27(4)); in respect of whom it is included
        # matters only when it is included.
        lcwra_included = benunit("uc_LCWRA_element", period) > 0
        lcwra_rank = person.get_rank(
            benunit, where(carer, 1_000, 0) - age, condition=limited_capability
        )
        lcwra_claimant = limited_capability & lcwra_included & (lcwra_rank == 0)
        qualifies = carer & ~lcwra_claimant
        # Reg. 29(2): both joint claimants "if they both qualify for it, but
        # only if they are not caring for the same severely disabled person";
        # reg. 29(3): otherwise one, by election or the Secretary of State.
        same_person = benunit("partners_care_for_same_severely_disabled_person", period)
        carer_rank = person.get_rank(benunit, -age, condition=qualifies)
        return qualifies & (~same_person | (carer_rank == 0))
