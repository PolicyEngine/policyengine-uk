from policyengine_uk.model_api import *


class housing_benefit_non_dep_deductions_claimant_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit claimant exempt from all non-dependant deductions"
    documentation = (
        "No deduction is made for any non-dependant if the claimant or partner "
        "is blind or receives Attendance Allowance, the DLA care component, the "
        "PIP daily living component or Armed Forces Independence Payment (SI "
        "2006/213 reg 74(6); SI 2006/214 reg 55(6)). Scottish disability "
        "assistance (pension age and adult disability payments, child "
        "disability payment, Scottish adult DLA) has no separate input."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        qualifying = (
            person("is_blind", period)
            | (person("attendance_allowance", period) > 0)
            | (person("dla_sc", period) > 0)
            | (person("pip_dl", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
        )
        return benunit.any(claimant_or_partner & qualifying)
