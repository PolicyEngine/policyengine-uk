from policyengine_uk.model_api import *

# Welfare benefits (Welfare Reform Act 2012 s. 96(10)) the benefit cap counts.
# Universal Credit counts Housing Benefit as nil (UC Regs 2013 reg. 80(2A))
# and Housing Benefit counts its own amount before the cap (HB Regs 2006
# reg. 75C(2)(b)). The model pays a family Universal Credit or Housing
# Benefit, never both, so one total serves both schemes.
CAPPED_BENEFITS = [
    "child_benefit",
    "child_tax_credit",
    "jsa_income",
    "income_support",
    "esa_income",
    "universal_credit_pre_benefit_cap",
    "housing_benefit_pre_benefit_cap",
    "jsa_contrib",
    "incapacity_benefit",
    "esa_contrib",
    "sda",
]


class benefit_cap_welfare_benefits(Variable):
    value_type = float
    entity = BenUnit
    label = "Welfare benefits counted by the benefit cap"
    documentation = (
        "The total of the welfare benefits the benefit cap compares with the "
        "Universal Credit or Housing Benefit cap (UC Regs 2013 regs. 79(1) "
        "and 80; HB Regs 2006 regs. 75A and 75C). Only the benefits of the "
        "single person or couple count (is_uc_assessed_claimant): a "
        "dependant's own benefits do not."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/96",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75C",
    )

    def formula(benunit, period, parameters):
        # The cap applies to "the welfare benefits to which a single person or
        # couple is entitled" (WRA 2012 s. 96(1); UC Regs 2013 reg. 80(1)), so
        # a dependant's own contributory benefit is not part of the total.
        claimants = benunit.members("is_uc_assessed_claimant", period)
        return add_for_members(benunit, period, CAPPED_BENEFITS, claimants)
