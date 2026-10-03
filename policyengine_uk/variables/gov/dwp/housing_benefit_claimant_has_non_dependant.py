from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.lha_renter_has_non_dependant import (
    has_non_dependant_in_benefit_unit,
)
from policyengine_uk.variables.household.consumption.rent.non_dependant_normally_resides_with import (
    non_dependants_residing_with,
)


class housing_benefit_claimant_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit claimant has a non-dependant residing with them"
    documentation = (
        "Whether a non-dependant resides with the claimant, for the young "
        "individual's shared accommodation rate: someone in the benefit unit "
        "who is neither a claimant or partner nor a child or young person, or "
        "a non-dependant of another family (see "
        "is_non_dependant_of_household_head) who normally resides with this "
        "family. In a household whose rent is shared, a non-dependant resides "
        "with each joint occupier given by non_dependant_normally_resides_with "
        "(by default all of them); otherwise with the household head's "
        "family. Joint tenants and other sharers of the rent, boarders and "
        "lodgers are not non-dependants."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf#page=33",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        within_benefit_unit = has_non_dependant_in_benefit_unit(benunit, period)
        # HB Regs 2006 reg 3(1), (2)(d)-(e) and (4): a non-dependant of
        # several joint occupiers resides with each of them (LHA Guidance
        # Manual paras 2.050 and 2.110); one who lives with one joint tenant
        # only resides with that tenant alone (para 2.093, example 2).
        non_dependant_claimants = person("is_claimant_or_partner", period) & person(
            "is_non_dependant_of_household_head", period
        )
        other_families = non_dependants_residing_with(
            benunit, period, non_dependant_claimants
        )
        return within_benefit_unit | (other_families > 0)
