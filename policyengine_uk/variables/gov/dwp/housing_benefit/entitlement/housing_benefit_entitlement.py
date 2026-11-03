from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income import (
    hb_income_before_deductions,
    housing_benefit_applicable_income,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_applicable_income_disregard import (
    hb_segment_deductions,
)
from policyengine_uk.variables.gov.dwp.housing_benefit.applicable_income.housing_benefit_specified_or_temporary_accommodation_disregard import (
    hb_accommodation_segments,
    hb_uses_annual_override,
)


class housing_benefit_entitlement(Variable):
    label = "Housing Benefit entitlement"
    documentation = (
        "The appropriate maximum Housing Benefit (the eligible rent less "
        "non-dependant deductions), less 65% of the excess of applicable "
        "income over the applicable amount. Where the Local Housing Allowance "
        "applies, the eligible rent is the maximum rent (LHA), which is the "
        "lower of the LHA rate and the rent, so the cap applies before the "
        "taper. When accommodation earnings disregards change within the "
        "fiscal year, calculate income floors, childcare/earnings limits, "
        "the income threshold, taper and zero-award floor separately in "
        "each segment, then combine completed awards. Annual earnings, rent, "
        "ages and household status remain constant. Other parameters keep "
        "the model's annual convention. Supplied annual income/deductions "
        "and replacement formulas retain their normal override semantics. "
        "Annual income intermediates are not period-specific assessments."
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
        "https://www.legislation.gov.uk/uksi/2026/753/regulation/1",
        "https://www.legislation.gov.uk/uksi/2026/978/regulation/2",
        "https://www.legislation.gov.uk/nisr/2026/157/regulation/2",
    )

    def formula(benunit, period, parameters):
        # Where a maximum rent (LHA) is determined, it is the eligible rent
        # (SI 2006/213 and SI 2006/214 reg 12D(2)(a); NI SR 2006/405 and
        # SR 2006/406 reg 13C(2)(a)). LHA_cap is the LHA rate or, where the
        # rent is lower, the rent (the cap rent: reg 13D(5); NI reg 14D(5)),
        # or the rent less meals after a rent officer's board and attendance
        # finding (reg 13C(5)(e), 13(7)). Otherwise charges for meals are not
        # eligible (reg 12B(2)(b) and Sch 1 paras 1(a)(i) and 2).
        rent_less_meals = max_(
            0,
            benunit("benunit_rent", period)
            - benunit("housing_benefit_meals_deduction", period),
        )
        lha_eligible = benunit("LHA_eligible", period)
        eligible_rent = where(lha_eligible, benunit("LHA_cap", period), rent_less_meals)
        # The appropriate maximum Housing Benefit is the eligible rent less
        # non-dependant deductions (SI 2006/213 reg 70, SI 2006/214 reg 50;
        # NI regs 68 and 48).
        non_dep_deductions = benunit("housing_benefit_non_dep_deductions", period)
        maximum_housing_benefit = eligible_rent - non_dep_deductions
        # 65% of the excess of income over the applicable amount is deducted
        # from the maximum (SSCBA 1992 s.130(3)(b), SI 2006/213 reg 71,
        # SI 2006/214 reg 51; NI: SSCB(NI)A 1992 s.129(3)(b), regs 69(b) and
        # 49(b)).
        applicable_amount = benunit("housing_benefit_applicable_amount", period)
        income = benunit("housing_benefit_applicable_income", period)
        withdrawal_rate = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.withdrawal_rate
        segments = list(hb_accommodation_segments(benunit, period, parameters))
        if len(segments) == 1 or hb_uses_annual_override(
            benunit,
            period,
            "housing_benefit_applicable_income",
            housing_benefit_applicable_income.formula,
        ):
            taper = max_(0, income - applicable_amount) * withdrawal_rate
            return max_(0, maximum_housing_benefit - taper)
        income_before_deductions = hb_income_before_deductions(
            benunit, period, parameters
        )
        retain_annual_income = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        ) | benunit("housing_benefit_on_passporting_benefit", period)
        annual_award = benunit.empty_array()
        for accommodation, share in segments:
            disregard, childcare = hb_segment_deductions(
                benunit, period, parameters, accommodation
            )
            segment_income = where(
                retain_annual_income,
                income,
                max_(0, income_before_deductions - disregard - childcare),
            )
            taper = max_(0, segment_income - applicable_amount) * withdrawal_rate
            annual_award = annual_award + share * max_(
                0, maximum_housing_benefit - taper
            )
        return annual_award
