from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    ALL_REQUIREMENTS,
    claimants,
    floor_applies,
)


class uc_mif_applies(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit minimum income floor applies"
    documentation = (
        "Whether the minimum income floor applies to this person: a claimant "
        "in gainful self-employment, outside a start-up period, who would "
        "apart from the floor and the earnings thresholds be subject to all "
        "work-related requirements."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/62"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Reg. 62(1) applies to a claimant, not a dependant, who (a) is in
        # gainful self-employment and (b) "would, apart from this regulation
        # or regulation 90, fall within section 22 of the Act". Reg. 62(5)
        # leaves out start-up periods.
        group = person("uc_work_related_group_apart_from_earnings", period)
        all_requirements = group == group.possible_values.ALL_REQUIREMENTS
        return claimants(person, period) & floor_applies(
            person, period, where(all_requirements, ALL_REQUIREMENTS, -1)
        )
