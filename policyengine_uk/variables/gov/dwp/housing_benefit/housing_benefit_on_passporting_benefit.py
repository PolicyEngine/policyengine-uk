from policyengine_uk.model_api import *


class housing_benefit_on_passporting_benefit(Variable):
    label = "on a benefit that passports the Housing Benefit means test"
    documentation = (
        "Whether this benefit unit is on Universal Credit, Income Support, "
        "income-based Jobseeker's Allowance or income-related Employment and "
        "Support Allowance, which disregards the whole of its earnings, other "
        "income and capital in the Housing Benefit means test. Income Support, "
        "income-based JSA and income-related ESA count when a positive amount "
        "is paid (in_receipt_of_income_support_jsa_ib_or_esa_ir). A person is "
        "on Universal Credit on any day they are entitled to it, whether it is "
        "in payment or not (SI 2006/213 and SR 2006/405 reg 2(3B)). The model "
        "reads that as Universal Credit above nil before the benefit cap and "
        "deductions (is_uc_entitled), for a family that claims it "
        "(would_claim_uc), so a Universal Credit award that the cap or "
        "deductions reduce to nil still counts. The model tests the year "
        "rather than each day, and both members of a joint claim are on "
        "Universal Credit. There is no age condition: the working-age "
        "regulations apply to a claimant over the qualifying age for State "
        "Pension Credit whose partner is on one of these benefits (reg "
        "5(1)(b)), and the model's Universal Credit needs a claimant or "
        "partner under the qualifying age for State Pension Credit in any "
        "case (is_uc_eligible). The "
        "universal credit limb applies from 28 October "
        "2013 in Great Britain and 8 May 2018 in Northern Ireland "
        "(gov.dwp.housing_benefit.means_test.universal_credit_passport)."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5/paragraph/4",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/2",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5/paragraph/12",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/6/paragraph/4",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7/paragraph/5",
    )

    def formula(benunit, period, parameters):
        p = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.universal_credit_passport
        country = benunit.household("country", period)
        # Great Britain's date applies everywhere but Northern Ireland,
        # including an unknown country.
        universal_credit_limb = where(
            country == country.possible_values.NORTHERN_IRELAND,
            p.northern_ireland,
            p.great_britain,
        )
        # Universal Credit before the benefit cap and deductions: Universal
        # Credit depends on Housing Benefit through the benefit cap
        # (benefit_cap_reduction), so reading the amount paid
        # (universal_credit) here would be circular. Before the cap is also
        # the law's reading: entitlement counts whether or not it is paid.
        on_universal_credit = benunit("is_uc_entitled", period) & universal_credit_limb
        on_legacy_benefit = benunit(
            "in_receipt_of_income_support_jsa_ib_or_esa_ir", period
        )
        return on_universal_credit | on_legacy_benefit
