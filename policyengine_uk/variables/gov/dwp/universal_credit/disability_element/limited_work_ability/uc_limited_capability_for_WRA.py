from policyengine_uk.model_api import *


class uc_limited_capability_for_WRA(Variable):
    value_type = bool
    entity = Person
    label = "Assessed to have limited capability for work-related activity"
    documentation = (
        "Whether this person has been assessed by the DWP as having limited "
        "capability for work and work-related activity. It defaults to "
        "is_disabled_for_benefits, which datasets derive from disability "
        "benefit receipt, ESA included. A determination of limited capability "
        "for work-related activity is what gives ESA its support component, "
        "and Universal Credit takes the ESA determination (UC Regs 2013 reg "
        "40(1)(a)(ii)). So a person whose own ESA award (has_own_esa_award) "
        "does not include the support component (esa_includes_support_"
        "component) is taken not to have it, whatever the flag, though someone "
        "still in the ESA assessment phase may yet be found to. The model does "
        "not infer it the other way, from the support component alone: the "
        "Universal Credit LCWRA element and work allowance still read every "
        "member of the benefit unit, not only the claimants. Users can set it "
        "directly."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/40",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/19",
    )

    def formula(person, period, parameters):
        esa_without_support_component = person("has_own_esa_award", period) & ~person(
            "esa_includes_support_component", period
        )
        return (
            person("is_disabled_for_benefits", period) & ~esa_without_support_component
        )
