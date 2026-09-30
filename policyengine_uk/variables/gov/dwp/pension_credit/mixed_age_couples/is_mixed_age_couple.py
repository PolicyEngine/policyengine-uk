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
        # The claimant and partner: adults other than a child or qualifying
        # young person for Pension Credit, so a pensioner with an 18 or 19
        # year old dependant in education is not a couple here.
        claimant_or_partner = person("is_adult", period) & ~person(
            "is_child_or_qualifying_young_person_for_pension_credit", period
        )
        pension_age = person("is_SP_age", period)
        n_pension_age = benunit.sum(claimant_or_partner & pension_age)
        return (benunit.sum(claimant_or_partner) == 2) & (n_pension_age == 1)
