from policyengine_uk.model_api import *


class uc_non_dep_deductions_renter_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit renter exempt from all housing cost contributions"
    documentation = (
        "No housing cost contribution is deducted for any non-dependant if the "
        "renter, or either joint renter of a couple, is blind or receives "
        "Attendance Allowance, the middle or highest rate of the DLA care "
        "component or the PIP daily living component. Scottish disability "
        "assistance (adult and pension age disability payments, child "
        "disability payment, Scottish adult DLA) has no separate input, and "
        "entitlement suspended in hospital is not modelled."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/15"

    def formula(benunit, period, parameters):
        # UC Regs 2013 Sch 4 para 15: "joint renters" are joint claimants
        # (para 1(2)), so the claimant and partner.
        person = benunit.members
        renter = person("is_claimant_or_partner", period)
        qualifying = (
            person("is_blind", period)
            | person("dla_sc_middle_plus", period)
            | (person("attendance_allowance", period) > 0)
            | (person("pip_dl", period) > 0)
        )
        return benunit.any(renter & qualifying)
