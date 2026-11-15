from policyengine_uk.model_api import *


class uc_is_ineligible_partner(Variable):
    value_type = bool
    entity = Person
    label = "Partner who cannot be a joint Universal Credit claimant"
    documentation = (
        "Whether this person is the member of a couple whose partner claims "
        "Universal Credit as a single person under the Universal Credit "
        "Regulations 2013 reg. 3(3): this person (a) is under 18 and not a "
        "person to whom the regulation 8 minimum age of 16 applies, (b) is "
        "not in Great Britain, (c) is a prisoner, (d) is excluded by "
        "regulation 19, or (e) is subject to immigration control. The model "
        "derives (a) from `meets_uc_minimum_age_condition`, treating a member "
        "under 16 as within (a) whatever their circumstances; (b) to (e) are "
        "not observed, so set this to true for such a partner. They are not "
        "a claimant (`is_uc_single_or_joint_claimant`): the award has a "
        "single claimant's amounts (reg. 36(3)), no element for their "
        "disability or caring, and they are in no work-related group, so the "
        "minimum income floor never applies to them. Their capital and "
        "income count as the claimant's (regs. 18(2) and 22(3)), and they add "
        "the pay for 35 hours at the national living wage to the couple "
        "threshold (reg. 90(3)(b))."
    )
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 3(3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 8",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/8",
        ),
    ]
    definition_period = YEAR

    def formula(person, period, parameters):
        # Reg. 3(3)(a): the other member "does not meet the basic condition
        # in section 4(1)(a) (at least 18 years old) and is not a person in
        # respect of whom the minimum age specified in regulation 8 applies".
        # From 16, failing the age condition means reg. 8 does not apply. A
        # member under 16 fails it even where reg. 8 applies; reg. 3(3)(a)
        # then strictly leaves the other member no single claim, which the
        # model does not follow. Where both members fail, neither can claim.
        couple = person("is_uc_assessed_claimant", period)
        in_couple = person.benunit.sum(couple) == 2
        return couple & in_couple & ~person("meets_uc_minimum_age_condition", period)
