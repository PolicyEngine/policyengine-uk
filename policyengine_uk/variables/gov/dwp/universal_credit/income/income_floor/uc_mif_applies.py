from policyengine_uk.model_api import *


class uc_mif_applies(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit minimum income floor applies"
    documentation = (
        "Whether the minimum income floor applies to this person: a claimant "
        "in gainful self-employment, outside a start-up period, who would "
        "apart from the floor and the earnings thresholds be subject to all "
        "work-related requirements. A start-up period is one supplied as an "
        "input, or the one that begins when a self-employed responsible "
        "carer enters the all work-related requirements group."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/62"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Reg. 62(1) applies to a claimant, not a dependant, who (a) is in
        # gainful self-employment and (b) "would, apart from this regulation
        # or regulation 90, fall within section 22 of the Act". Only a
        # claimant has a work-related group.
        group = person("uc_work_related_group_apart_from_earnings", period)
        all_requirements = group == group.possible_values.ALL_REQUIREMENTS
        gainfully_self_employed = person("uc_is_in_gainful_self_employment", period)
        # Reg. 62(5) leaves out assessment periods in a start-up period:
        # one the data or household supply, or the one that begins on
        # entering the all work-related requirements group.
        in_startup_period = person("uc_is_in_startup_period", period) | person(
            "uc_is_in_startup_period_on_entering_all_requirements_group", period
        )
        return all_requirements & gainfully_self_employed & ~in_startup_period
