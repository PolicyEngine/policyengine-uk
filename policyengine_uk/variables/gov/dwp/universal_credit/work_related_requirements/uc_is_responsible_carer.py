from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    claimants,
    combined_earned_income,
)


class uc_is_responsible_carer(Variable):
    value_type = bool
    entity = Person
    label = "Responsible carer for a child, for Universal Credit"
    documentation = (
        "Whether the person is the responsible carer for the children in "
        "their benefit unit: a single claimant who is responsible for a "
        "child, or the member of a couple whom the couple have jointly "
        "nominated. Only one joint claimant can be nominated, and the "
        "nomination covers all their children. Datasets and households "
        "should supply the nomination where they know it. Without one, the "
        "model takes the nomination that leaves the couple the lower "
        "combined earned income after the minimum income floor, which is the "
        "nomination that gives them the higher award: the choice is the "
        "couple's. Where the nomination makes no difference the elder "
        "claimant is the responsible carer."
    )
    reference = [
        dict(
            title="Welfare Reform Act 2012 s. 19(6)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/19",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 86",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/86",
        ),
    ]
    definition_period = YEAR

    def formula(person, period, parameters):
        claimant = claimants(person, period)
        # s. 19(6): a single person who is responsible for the child, or the
        # nominated member of a couple either of whom is responsible for it.
        has_child = person.benunit("uc_youngest_child_age", period) < np.inf
        rank = person.get_rank(person.benunit, -person("age", period), claimant)
        elder = claimant & (rank == 0)
        younger = claimant & (rank == 1)
        # Reg. 86(2) and (4): the couple choose which of them to nominate.
        # The floor is the only consequence of the choice in the model.
        if_elder = combined_earned_income(person, period, parameters, elder)
        if_younger = combined_earned_income(person, period, parameters, younger)
        nominate_younger = person.benunit.any(younger) & (if_younger < if_elder)
        return has_child & where(nominate_younger, younger, elder)
