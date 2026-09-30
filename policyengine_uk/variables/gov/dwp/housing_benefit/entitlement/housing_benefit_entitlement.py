from policyengine_uk.model_api import *


class housing_benefit_entitlement(Variable):
    label = "Housing Benefit entitlement"
    documentation = (
        "The appropriate maximum Housing Benefit (the eligible rent less "
        "non-dependant deductions), less 65% of the excess of applicable "
        "income over the applicable amount. Where the Local Housing Allowance "
        "applies, the eligible rent is the maximum rent (LHA), which is the "
        "lower of the LHA rate and the rent, so the cap applies before the "
        "taper."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/130",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/70",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/71",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/12D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/50",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/51",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/129",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/13C",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/14D",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/68",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/69",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/13C",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/14D",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/48",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/49",
    )

    def formula(benunit, period, parameters):
        # Where a maximum rent (LHA) is determined, it is the eligible rent
        # (SI 2006/213 and SI 2006/214 reg 12D(2)(a); NI SR 2006/405 and
        # SR 2006/406 reg 13C(2)(a)). LHA_cap is the LHA rate or, where the
        # rent is lower, the rent (the cap rent: reg 13D(5); NI reg 14D(5)).
        rent = benunit("benunit_rent", period)
        lha_eligible = benunit("LHA_eligible", period)
        eligible_rent = where(lha_eligible, benunit("LHA_cap", period), rent)
        # The appropriate maximum Housing Benefit is the eligible rent less
        # non-dependant deductions (SI 2006/213 reg 70, SI 2006/214 reg 50;
        # NI regs 68 and 48).
        non_dep_deductions = benunit("housing_benefit_non_dep_deductions", period)
        maximum_housing_benefit = eligible_rent - non_dep_deductions
        # 65% of the excess of income over the applicable amount is deducted
        # from the maximum (SSCBA 1992 s.130(3)(b), SI 2006/213 reg 71,
        # SI 2006/214 reg 51; NI: 1992 Act s.129(3)(b), regs 69(b) and 49(b)).
        applicable_amount = benunit("housing_benefit_applicable_amount", period)
        income = benunit("housing_benefit_applicable_income", period)
        withdrawal_rate = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.withdrawal_rate
        taper = max_(0, income - applicable_amount) * withdrawal_rate
        return max_(0, maximum_housing_benefit - taper)
