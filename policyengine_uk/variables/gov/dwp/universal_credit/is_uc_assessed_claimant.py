from policyengine_uk.model_api import *


class is_uc_assessed_claimant(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit claimant whose income is assessed"
    documentation = (
        "The single claimant, or one of the two members of the couple, whose "
        "income a Universal Credit award assesses: `is_uc_claimant`, limited "
        "to the two eldest. Universal Credit deducts the income of the "
        "claimant, or the combined income of joint claimants; where a member "
        "of a couple claims as a single person, their partner's income counts "
        "as if they were joint claimants. A child's or qualifying young "
        "person's income is theirs, not the claimant's, and does not count; "
        "nor does the income of anyone else in the benefit unit. Who the "
        "claimants are comes from `is_uc_claimant`: a member it flags is "
        "taken as a claimant, whatever their age."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 2(1)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/2",
        ),
        dict(
            title="Welfare Reform Act 2012 s. 8(4)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/8",
        ),
        dict(
            title="Welfare Reform Act 2012 s. 40",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/40",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 22(1) and (3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
        ),
    ]

    def formula(person, period, parameters):
        # A claim is made by a single person or jointly by the two members of
        # a couple (WRA 2012 s. 2(1)), and "claimant" means a single claimant
        # or each of joint claimants (s. 40), so there are at most two.
        # is_uc_claimant flags at most two unless inputs flag more; then the
        # two eldest are the claimants, and members of the same age rank in
        # the order the people are entered.
        claimant = person("is_uc_claimant", period)
        age = person("age", period)
        rank = person.get_rank(person.benunit, -age, condition=claimant)
        return claimant & (rank < 2)
