from policyengine_uk.model_api import *


class council_tax_reduction_applicant_has_non_dep_exemption(Variable):
    value_type = bool
    entity = BenUnit
    label = "No non-dependant deductions from this family's Council Tax Reduction"
    documentation = (
        "Whether no deduction is made for any non-dependant from this family's "
        "Council Tax Reduction because the applicant or partner is blind, or "
        "receives Attendance Allowance, the care component of Disability "
        "Living Allowance, the daily living component of Personal "
        "Independence Payment or Armed Forces Independence Payment. The "
        "exemption belongs to each applicant: where families share the rent "
        "and each claims, one family's disability does not exempt another's "
        "claim. The model applies it in the English working-age local "
        "schemes; a household with a single claim uses "
        "council_tax_reduction_household_has_non_dep_exemption."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/30",
    )

    def formula(benunit, period, parameters):
        # SI 2012/2885 Sch 1 para 8(6): no deduction for non-dependants
        # "if the applicant or his partner is" blind or receiving one of the
        # listed benefits.
        person = benunit.members
        applicant_or_partner = person("is_claimant_or_partner", period)
        exempting = (
            person("is_blind", period)
            | (person("attendance_allowance", period) > 0)
            | (person("pip_dl", period) > 0)
            | (person("dla_sc", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
        )
        return benunit.any(applicant_or_partner & exempting)
