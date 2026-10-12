from policyengine_uk.model_api import *
from numpy import ceil


class partners_unused_personal_allowance(Variable):
    label = "Partner's unused personal allowance"
    reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/55B"
    documentation = (
        "The personal tax allowance not used by this person's partner, if they exist"
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        # Only a spouse or civil partner can transfer allowance (ITA 2007
        # s.55B(5A), s.55C(1)(a)): the other claimant or partner of the
        # benefit unit, never a child. People outside the couple get zero, so
        # they cannot produce a negative transferable amount.
        couple_member = person("is_claimant_or_partner", period)
        pa = person("unused_personal_allowance", period)
        return person.benunit.sum(couple_member * pa) - couple_member * pa
