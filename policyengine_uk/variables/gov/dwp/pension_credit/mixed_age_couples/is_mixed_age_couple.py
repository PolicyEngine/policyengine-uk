from policyengine_uk.model_api import *


class is_mixed_age_couple(Variable):
    value_type = bool
    entity = BenUnit
    label = "Mixed-age couple"
    documentation = (
        "A couple one member of which has reached the qualifying age for State "
        "Pension Credit and the other of which has not."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2019/37/article/2",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/4",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # Every adult in the benefit unit stands in for the claimant and
        # partner, as in is_pension_credit_eligible and is_uc_eligible, so a
        # pensioner couple with an 18 or 19 year old dependant also counts.
        adult = person("is_adult", period)
        pension_age = person("is_SP_age", period)
        n_pension_age = benunit.sum(adult & pension_age)
        return (
            benunit("is_couple", period)
            & (n_pension_age > 0)
            & (n_pension_age < benunit.sum(adult))
        )
