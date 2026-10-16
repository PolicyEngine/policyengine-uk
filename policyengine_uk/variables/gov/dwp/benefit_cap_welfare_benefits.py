from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_cap import benefit_cap_couple
from policyengine_uk.utils.benefit_unit import award_of_members
from policyengine_uk.variables.gov.dwp.esa_income import income_related_esa_award
from policyengine_uk.variables.gov.dwp.jsa_income import income_related_jsa_award

# Welfare benefits (Welfare Reform Act 2012 s. 96(10)) the benefit cap counts.
# The cap counts those "to which the single person or couple is entitled" (UC
# Regs 2013 regs 79(1), 80(1); HB Regs 2006 reg 75A): the claimant's and
# partner's own awards, and the awards made to the family. Another member of
# the benefit unit, such as a non-dependent adult, is entitled to their own
# contributory or income-related benefit; it still counts in household income.
# Housing Benefit counts its own amount before the cap (HB Regs 2006
# reg. 75C(2)(b)), so this total includes it. Universal Credit counts Housing
# Benefit as nil (UC Regs 2013 reg. 80(2A)): uc_benefit_cap_reduction takes it
# out. Universal Credit before the cap is in the total too; a family receiving
# it is outside the Housing Benefit cap (HB Regs 2006 reg. 75F(1)(g)). With
# those two adjustments one total serves both schemes. Reg. 75C(2)(a) counts
# Housing Benefit for specified accommodation as nil; the model's input
# in_specified_or_temporary_accommodation does not separate specified from
# temporary accommodation, so that Housing Benefit is counted at its amount
# before the cap.
CLAIMANT_OR_PARTNER_BENEFITS = [
    "jsa_contrib",
    "esa_contrib",
    "incapacity_benefit",
    "sda",
]
FAMILY_BENEFITS = [
    "child_benefit",
    "child_tax_credit",
    "income_support",
    "universal_credit_pre_benefit_cap",
    "housing_benefit_pre_benefit_cap",
]


class benefit_cap_welfare_benefits(Variable):
    value_type = float
    entity = BenUnit
    label = "Welfare benefits counted by the benefit cap"
    documentation = (
        "The total of the welfare benefits the benefit cap compares with the "
        "Universal Credit or Housing Benefit cap (UC Regs 2013 regs. 79(1) "
        "and 80; HB Regs 2006 regs. 75A and 75C): those the claimant or "
        "couple is entitled to. For a family on Universal Credit the couple "
        "is its claimants (is_uc_assessed_claimant), including the other "
        "member of a couple where one member claims as a single person; "
        "otherwise it is the claimant and partner (is_claimant_or_partner). "
        "The two are the same unless is_uc_claimant is entered. Benefits "
        "another member of the benefit unit claims in their own right do not "
        "count. The total includes Universal Credit and Housing Benefit "
        "before the cap (universal_credit_pre_benefit_cap, "
        "housing_benefit_pre_benefit_cap). Universal Credit counts Housing "
        "Benefit as nil (UC Regs 2013 reg. 80(2A)), so "
        "uc_benefit_cap_reduction subtracts it; an entered total should "
        "include it. Maternity allowance and the bereavement benefits, also "
        "welfare benefits, are not modelled here."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/96",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/78",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75A",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75C",
    )

    def formula(benunit, period, parameters):
        # The couple of the scheme whose award the family has
        # (benefit_cap_couple).
        couple = benefit_cap_couple(benunit, period)
        # Income-based JSA and income-related ESA are awarded to the benefit
        # unit; the couple's part is read from their reports, as in
        # claimant_or_partner_jsa_income and claimant_or_partner_esa_income.
        income_based = award_of_members(
            benunit,
            period,
            "jsa_income",
            "jsa_income_reported",
            income_related_jsa_award,
            couple,
        ) + award_of_members(
            benunit,
            period,
            "esa_income",
            "esa_income_reported",
            income_related_esa_award,
            couple,
        )
        return income_based + add_for_members(
            benunit,
            period,
            CLAIMANT_OR_PARTNER_BENEFITS + FAMILY_BENEFITS,
            couple,
        )
