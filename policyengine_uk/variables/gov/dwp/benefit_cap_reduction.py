from policyengine_uk.model_api import *

# Welfare benefits (Welfare Reform Act 2012 s.96(10)) the model has. The cap
# counts those "to which the single person or couple is entitled" (UC Regs
# 2013 regs 79(1), 80(1); HB Regs 2006 reg 75A): the claimant's and partner's
# own awards, and the awards made to the family. Another member of the
# benefit unit, such as a non-dependent adult, is entitled to their own
# contributory or income-related benefit; it still counts in household income.
CLAIMANT_OR_PARTNER_BENEFITS = [
    "jsa_contrib",
    "esa_contrib",
    "incapacity_benefit",
    "sda",
]
FAMILY_BENEFITS = [
    "child_benefit",
    "child_tax_credit",
    "claimant_or_partner_jsa_income",
    "income_support",
    "claimant_or_partner_esa_income",
    "universal_credit_pre_benefit_cap",
    "housing_benefit_pre_benefit_cap",
]


class benefit_cap_reduction(Variable):
    label = "benefit cap reduction"
    documentation = (
        "The amount by which the welfare benefits the claimant or couple is "
        "entitled to exceed the benefit cap. Benefits another member of the "
        "benefit unit claims in their own right do not count. Maternity "
        "allowance and the bereavement benefits, also welfare benefits, are "
        "not modelled here."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/96",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75A",
    )

    def formula(benunit, period, parameters):
        claimant = benunit.members("is_claimant_or_partner", period)
        capped = add_for_members(
            benunit,
            period,
            CLAIMANT_OR_PARTNER_BENEFITS + FAMILY_BENEFITS,
            claimant,
        )
        return max_(capped - benunit("benefit_cap", period), 0)
