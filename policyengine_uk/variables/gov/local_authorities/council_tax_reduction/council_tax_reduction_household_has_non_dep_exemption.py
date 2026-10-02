from policyengine_uk.model_api import *


class council_tax_reduction_household_has_non_dep_exemption(Variable):
    value_type = bool
    entity = Household
    label = "CTR household has a non-dependant deduction exemption"
    documentation = (
        "Whether no non-dependant deduction is made from the household head's "
        "family's Council Tax Reduction because the applicant or partner "
        "(is_council_tax_reduction_applicant_or_partner) is blind or receives "
        "Attendance Allowance, the care component of Disability Living "
        "Allowance, the daily living component of Personal Independence "
        "Payment or Armed Forces Independence Payment."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8"

    def formula(household, period, parameters):
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        # SI 2012/2885 Sch 1 para 8(6): "the applicant or his partner".
        claimant_or_partner = claimant_benunit & person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        is_blind = person("is_blind", period) & claimant_or_partner
        attendance_allowance = (
            person("attendance_allowance", period) > 0
        ) & claimant_or_partner
        pip_daily_living = (person("pip_dl", period) > 0) & claimant_or_partner
        dla_care = (person("dla_sc", period) > 0) & claimant_or_partner
        armed_forces_independence_payment = (
            person("armed_forces_independence_payment", period) > 0
        ) & claimant_or_partner
        return household.any(
            is_blind
            | attendance_allowance
            | pip_daily_living
            | dla_care
            | armed_forces_independence_payment
        )
