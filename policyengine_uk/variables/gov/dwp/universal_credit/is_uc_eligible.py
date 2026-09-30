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
        # No family gets both Pension Credit and Universal Credit (UC
        # (Transitional Provisions) Regs 2014 reg 5(1)(d)). A mixed-age couple
        # keeping the SI 2019/37 saving could still choose Universal Credit
        # jointly (UC Regs 2013 reg 3(2)(a)) and lose the saving; the model
        # keeps it on the Pension Credit route, anchored to its reported
        # Pension Credit or Housing Benefit. That, and routing mixed-age
        # couples not reported on Universal Credit to Pension Credit before
        # 15 May 2019, are modelling choices.
        pension_credit_route = benunit("meets_pension_credit_age_conditions", period)
        return has_working_age_adult & ~pension_credit_route & (capital <= limit)
