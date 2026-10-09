from policyengine_uk.model_api import *


class housing_benefit_non_dep_deduction_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "No non-dependant deductions from this family's Housing Benefit"
    documentation = (
        "Whether no deduction is made for any non-dependant from this "
        "family's Housing Benefit because the claimant or partner is blind, "
        "or receives Attendance Allowance, the care component of Disability "
        "Living Allowance, the daily living component of Personal "
        "Independence Payment or Armed Forces Independence Payment. The "
        "Scottish equivalents listed in the regulation (Pension Age "
        "Disability Payment, Child and Adult Disability Payment, Scottish "
        "Adult Disability Living Allowance) are not modelled separately."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(benunit, period, parameters):
        # HB Regs 2006 reg 74(6); SPC Regs 2006 reg 55(6): no deduction for
        # any non-dependant if the claimant or partner is blind or receiving
        # one of the listed benefits in respect of himself.
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        exempting = (
            person("is_blind", period)
            | (person("attendance_allowance", period) > 0)
            | (person("pip_dl", period) > 0)
            | (person("dla_sc", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
        )
        return benunit.any(claimant_or_partner & exempting)
