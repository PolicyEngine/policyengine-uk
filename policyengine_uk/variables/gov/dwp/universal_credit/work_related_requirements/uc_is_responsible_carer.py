from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import claimants


class uc_is_responsible_carer(Variable):
    value_type = bool
    entity = Person
    label = "Responsible carer for a child, for Universal Credit"
    documentation = (
        "Whether the person is the responsible carer for the children in "
        "their benefit unit: a single claimant who is responsible for a "
        "child, or the member of a couple whom the couple have jointly "
        "nominated. Only one joint claimant can be nominated, and the "
        "nomination covers all their children. The nomination is the "
        "couple's choice: datasets and households should supply it where "
        "they know it. Without one, the model takes the claimant who works "
        "fewer hours as the main carer, and the elder where their hours are "
        "the same. `hours_worked` is an input that defaults to 0, so for a "
        "couple entered without hours the default falls to the elder: "
        "calculator and API users should set `uc_is_responsible_carer` (or "
        "each member's hours) for a couple with a child."
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
        # Reg. 86(2): "Only one of joint claimants may be nominated". The
        # default nomination is the claimant with fewer hours of paid work,
        # then the elder. A single claimant is the only candidate.
        hours = person("hours_worked", period)
        fewest_hours = person.benunit.min(where(claimant, hours, np.inf))
        candidate = claimant & (hours == fewest_hours)
        eldest = person.get_rank(person.benunit, -person("age", period), candidate) == 0
        return has_child & candidate & eldest
