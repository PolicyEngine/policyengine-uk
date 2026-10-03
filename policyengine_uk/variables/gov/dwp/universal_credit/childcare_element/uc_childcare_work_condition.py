from policyengine_uk.model_api import *


class uc_childcare_work_condition(Variable):
    value_type = bool
    entity = BenUnit
    label = "Meets Universal Credit childcare work condition"
    documentation = (
        "Regulation 32(1): the claimant is in paid work or has an offer of "
        "paid work due to start before the end of the next assessment period, "
        "and, for a couple, the other member is either in paid work or unable "
        "to provide childcare because they have limited capability for work, "
        "have regular and substantial caring responsibilities for a severely "
        "disabled person, or are temporarily absent from the claimant's "
        "household. Each joint claimant is a claimant, so the condition is met "
        "when one member meets limb (a) and the other meets limb (b). Paid "
        "work is the in_work proxy (positive hours or earnings in the year), "
        "or being treated as in paid work under regulation 32(2) "
        "(uc_childcare_treated_as_in_paid_work). The exceptions use the "
        "approximations in uc_unable_to_provide_childcare. Dependants are not "
        "tested."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 32",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/32",
        ),
        dict(
            title="Advice for Decision Making ch. F7, paras. F7011-F7015",
            href="https://assets.publishing.service.gov.uk/media/696a076c7b7f37aa8e4022d9/adm-ch-f7.pdf",
        ),
    ]

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant = person("is_uc_claimant", period)
        in_paid_work = person("in_work", period) | person(
            "uc_childcare_treated_as_in_paid_work", period
        )
        # Reg. 32(1)(a): in paid work or has an offer of paid work due to
        # start before the end of the next assessment period.
        meets_claimant_limb = in_paid_work | person(
            "uc_has_offer_of_paid_work_starting_by_end_of_next_assessment_period",
            period,
        )
        # Reg. 32(1)(b): the other member is in paid work or is unable to
        # provide childcare for a reason in (i)-(iii). An offer of paid work
        # satisfies limb (a) only.
        meets_other_member_limb = in_paid_work | person(
            "uc_unable_to_provide_childcare", period
        )
        # Joint claimants are each "the claimant" (WRA 2012 s. 40), so the
        # condition holds if any claimant meets limb (a) while every other
        # claimant meets limb (b). A single claimant has no other member.
        fails_other_member_limb = claimant & ~meets_other_member_limb
        others_failing = (
            benunit.project(benunit.sum(fails_other_member_limb))
            - fails_other_member_limb
        )
        return benunit.any(claimant & meets_claimant_limb & (others_failing == 0))
