from policyengine_uk.model_api import *


class is_uc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for the Universal Credit"
    documentation = "Whether this family is eligible for Universal Credit"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/5",
    )

    def formula(benunit, period, parameters):
        capital = benunit("uc_assessable_capital", period)
        limit = parameters(period).gov.dwp.universal_credit.means_test.capital.limit
        has_working_age_adult = benunit.any(benunit.members("is_WA_adult", period))
        # A family on the Pension Credit route cannot also have Universal
        # Credit (UC (Transitional Provisions) Regs 2014 reg 5(1)(d)). This
        # sends mixed-age couples keeping the SI 2019/37 saving, and every
        # mixed-age couple before 15 May 2019, to Pension Credit.
        pension_credit_route = benunit("meets_pension_credit_age_conditions", period)
        return has_working_age_adult & ~pension_credit_route & (capital <= limit)
