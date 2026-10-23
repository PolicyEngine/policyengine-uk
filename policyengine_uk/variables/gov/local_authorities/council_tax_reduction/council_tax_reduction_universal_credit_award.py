from policyengine_uk.model_api import *


class council_tax_reduction_universal_credit_award(Variable):
    value_type = bool
    entity = BenUnit
    label = "Council Tax Reduction applicant has an award of Universal Credit"
    documentation = (
        "Whether the Council Tax Reduction applicant or partner has an award "
        "of Universal Credit: Universal Credit is paid, or the family claims "
        "it and is entitled before the benefit cap and deductions, which "
        "reduce an award rather than end it (UC Regs 2013 reg 81; Oxford's "
        "scheme, Appendix 3, covers applicants who would be awarded it but "
        "for deductions). A supplied universal_credit amount counts as an "
        "award. From 1 April 2025 the Scottish scheme also counts an award "
        "reduced to zero by a sanction and one whose entitlement ended after "
        "a nil award due to earnings but is treated as reclaimed (SSI "
        "2021/249 reg 10A); neither is modelled. The benefit unit's award "
        "belongs to its claimant and partner, "
        "so it is not the applicant's where the household head applies "
        "alone. The schemes' working-age Universal Credit rules (the "
        "Secretary of State's assessments of income and capital, and the "
        "Universal Credit assumed yield) apply only to an applicant who is "
        "not a pensioner (council_tax_reduction_pensioner)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/81",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/37",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/26",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/10A",
    )

    def formula(benunit, period, parameters):
        paid = benunit("universal_credit", period) > 0
        entitled_claimant = benunit("claims_universal_credit", period) & benunit(
            "is_uc_entitled", period
        )
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        return (paid | entitled_claimant) & ~head_applies_alone
