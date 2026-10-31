from policyengine_uk.model_api import *


class oxford_council_tax_reduction_universal_credit_other_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Oxford Council Tax Reduction other income of a Universal Credit applicant"
    documentation = (
        "The yearly other (unearned) income that Oxford's working-age scheme "
        "adds to DWP's net earned income and the Universal Credit awarded for "
        "an applicant who receives Universal Credit (Appendix 3). Appendix 3 "
        "lists the income it ignores and takes all other unearned income into "
        "account; Appendix 5's disregards, Child Benefit and child maintenance "
        "among them, apply only to applicants without Universal Credit. "
        "gov.local_authorities.oxford.council_tax_reduction.universal_credit."
        "other_income_sources lists the sources and the reason for each. It "
        "counts Child Benefit, child maintenance and the receipts in Universal "
        "Credit's unearned income, and leaves out Universal Credit's assumed "
        "yield from capital (uc_tariff_income) and income derived from capital, "
        "which Part 1 para 30 and Annex 7 treat as capital. The income is the "
        "applicant's and partner's, as in "
        "council_tax_reduction_applicable_income: a household head who applies "
        "alone counts only their own, and the benefit unit's awards belong to its "
        "claimant and partner. The model does not count student loans or "
        "grants, which Annex 8 counts with its own disregards."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27",
        "https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27/3",
        "https://www.oxford.gov.uk/council-tax-reduction/council-tax-reduction-scheme-2026-27/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/66",
    )

    def formula(benunit, period, parameters):
        p = parameters(
            period
        ).gov.local_authorities.oxford.council_tax_reduction.universal_credit
        # Appendix 3 bases the income on "the income of the applicant and,
        # where appropriate, their partner". A person's receipts count for
        # the applicant and partner only. The benefit unit's awards (Child
        # Benefit and the rest) are its claimant's and partner's, so they do
        # not count where the household head applies alone.
        person = benunit.members
        applicant_or_partner = person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        applicant_family = ~benunit("council_tax_reduction_head_applies_alone", period)
        income = 0
        for source in p.other_income_sources:
            if person.entity.get_variable(source).entity.is_person:
                income = income + benunit.sum(
                    person(source, period) * applicant_or_partner
                )
            else:
                income = income + benunit(source, period) * applicant_family
        return income
