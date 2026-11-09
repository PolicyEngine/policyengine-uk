from policyengine_uk.model_api import *


class uc_non_dep_deductions_renter_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit renter exempt from all housing cost contributions"
    documentation = (
        "Under the Universal Credit Regulations 2013 Sch 4 para 15, the "
        "Secretary of State deducts no housing cost contribution for any "
        "non-dependant where the renter, or either joint renter, is blind, "
        "receives the middle or highest rate of the DLA care component, "
        "receives the PIP daily living component, or is 'a person in receipt "
        "of attendance allowance' (para 15(2)(c)). Para 1(2) calls the "
        "claimants 'renters' and joint claimants 'joint renters', so the "
        "formula reads is_uc_single_or_joint_claimant: a partner who cannot "
        "be a joint claimant, and whose partner claims as a single person "
        "under reg 3(3), brings no exemption. Para 15(2)(c) carries reg 2's "
        "definition of attendance allowance, whose heads include (a) "
        "attendance allowance under section 64 of the Contributions and "
        "Benefits Act and (f) armed forces independence payment. The formula "
        "reads uc_receives_attendance_allowance, which counts heads (a) and "
        "(f) and no other head, because the model holds no separate amount "
        "for heads (b), (d) and (e). Scottish disability assistance (adult "
        "and pension age disability payments, child disability payment, "
        "Scottish adult DLA) has no separate input, and the formula does not "
        "follow entitlement that a hospital stay suspends (para 15(2)(e))."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/15",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
    )

    def formula(benunit, period, parameters):
        # Sch 4 para 1(2): "renters" are the claimants and "joint renters"
        # the joint claimants, so a partner whom reg 3(3) leaves out of the
        # claim is neither.
        person = benunit.members
        renter = person("is_uc_single_or_joint_claimant", period)
        qualifying = (
            person("is_blind", period)
            | person("dla_sc_middle_plus", period)
            # Para 15(2)(c) uses "attendance allowance" as reg 2 defines it.
            | person("uc_receives_attendance_allowance", period)
            | (person("pip_dl", period) > 0)
        )
        return benunit.any(renter & qualifying)
