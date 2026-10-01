from policyengine_uk.model_api import *


class council_tax_reduction_applicant_has_non_dep_exemption(Variable):
    value_type = bool
    entity = BenUnit
    label = "No non-dependant deductions from this family's Council Tax Reduction"
    documentation = (
        "Whether no deduction is made for any non-dependant from this family's "
        "Council Tax Reduction because the applicant or partner is blind, or "
        "receives in respect of themselves Attendance Allowance, the care "
        "component of Disability Living Allowance, the daily living component "
        "of Personal Independence Payment or Armed Forces Independence Payment. "
        "The exemption belongs to each applicant: where families share the "
        "rent and each claims, one family's disability does not exempt "
        "another's claim. The model applies it in the English working-age "
        "local schemes."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/30",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
    )

    def formula(benunit, period, parameters):
        # SI 2012/2885 Sch 1 para 8(6): "No deduction is to be made in respect
        # of any non-dependants occupying an applicant's dwelling if the
        # applicant or his partner is" blind or receiving one of the listed
        # benefits "in respect of himself".
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
