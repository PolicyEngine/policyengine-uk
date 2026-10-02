from policyengine_uk.model_api import *


class uc_limited_capability_for_WRA(Variable):
    value_type = bool
    entity = Person
    label = "Assessed to have limited capability for work-related activity"
    documentation = (
        "Whether this person has been assessed by the DWP as having limited "
        "capability for work and work-related activity. Universal Credit takes "
        "an ESA determination of limited capability for work-related activity "
        "(UC Regs 2013 reg 40(1)(a)(ii); UC (Transitional Provisions) Regs "
        "2014 reg 19(4)), and that determination is what gives an ESA award "
        "its support component. So for a person with an ESA award of their "
        "own (has_own_esa_award) the model infers it from "
        "esa_includes_support_component: with the component they have it; "
        "without it they are taken not to, though someone still in the ESA "
        "assessment phase may yet be found to have it. For anyone else it "
        "defaults to is_disabled_for_benefits, which datasets derive from "
        "disability benefit receipt. Users can set it directly."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/40",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/19",
    )

    def formula(person, period, parameters):
        return where(
            person("has_own_esa_award", period),
            person("esa_includes_support_component", period),
            person("is_disabled_for_benefits", period),
        )
