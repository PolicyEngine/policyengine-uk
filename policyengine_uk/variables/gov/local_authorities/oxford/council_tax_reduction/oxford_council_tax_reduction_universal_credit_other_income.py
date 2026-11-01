from policyengine_uk.model_api import *


class oxford_council_tax_reduction_universal_credit_other_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Oxford Council Tax Reduction other income of a Universal Credit applicant"
    documentation = (
        "The yearly other (unearned) income that Oxford City Council adds to "
        "DWP's net earned income and the Universal Credit awarded for a "
        "working-age applicant who receives Universal Credit (Appendix 3). The "
        "council lists the income it ignores in Appendix 3 and takes all other "
        "unearned income into account; it applies its Appendix 5 disregards, "
        "Child Benefit and child maintenance among them, only to applicants "
        "without Universal Credit. "
        "gov.local_authorities.oxford.council_tax_reduction.universal_credit."
        "other_income_sources lists the sources and the reason for each. The "
        "model counts Child Benefit, child maintenance, the receipts DWP counts "
        "as Universal Credit unearned income, the Scottish Carer Supplement "
        "and the other receipts the council does not ignore. It leaves out "
        "Universal Credit's assumed yield from capital (uc_tariff_income), "
        "income derived from capital, which the council treats as capital "
        "(Part 1 para 30 and Annex 7), and miscellaneous income, which DWP "
        "already counts in its net earned income. The model counts the "
        "applicant's and partner's income, as in "
        "council_tax_reduction_applicable_income: a household head who applies "
        "alone counts only their own, and the benefit unit's awards belong to "
        "its claimant and partner. The model does not count student loans or "
        "grants, which the council counts under Annex 8 with its own "
        "disregards."
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
        # Oxford City Council bases the income on "the income of the
        # applicant and, where appropriate, their partner" (Appendix 3), so
        # the model counts a person's receipts for the applicant and partner
        # only. The benefit unit's awards (Child Benefit and the rest) belong
        # to its claimant and partner, so the model leaves them out where the
        # household head applies alone.
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
