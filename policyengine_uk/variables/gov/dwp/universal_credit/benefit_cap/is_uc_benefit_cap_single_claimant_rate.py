from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_unit import has_sixteen_year_old_dependant


class is_uc_benefit_cap_single_claimant_rate(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit benefit cap single claimant rate applies"
    documentation = (
        "Whether the Universal Credit claimant is a single claimant who is "
        "not responsible for a child or qualifying young person (UC Regs 2013 "
        "reg. 80A(2)(a) and (c)). Joint claimants, and a single claimant "
        "responsible for a child or qualifying young person, have the other "
        "rate. A member of a couple who claims as a single person because the "
        "other member cannot be a joint claimant (reg. 3(3)) is a single "
        "claimant (ADM E5007 note 3), although the welfare benefits capped "
        "are still the couple's (regs. 78(2) and 79(1)). A 16-year-old member "
        "counts as a qualifying young person for the year (reg. 5(1)(a))."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80A",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/78",
    )

    def formula(benunit, period, parameters):
        single_claimant = ~benunit("is_couple", period) | benunit(
            "uc_member_of_couple_claims_as_single_person", period
        )
        responsible = benunit(
            "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
            period,
        ) | has_sixteen_year_old_dependant(benunit, period)
        return single_claimant & ~responsible
