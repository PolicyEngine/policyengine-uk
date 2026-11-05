"""Budget 2026's company car tax rates for 2030-31.

Budget 2026 sets every company car appropriate percentage for 2030-31 one
point above 2029-30's, zero-emission cars included, and raises the maximum
from 39% to 40% (ITEPA 2003 s. 139(1), (3)(a) and (3)(b), and the diesel
cap in s. 141(2) step 3). Finance Bill 2026-27 is to legislate it, so the
baseline keeps 2029-30's rates for 2030-31 and this scenario applies the
rise from 6 April 2030. Table 6.1 of Budget 2026 (row 86) costs it at
+£310m in 2030-31 and +£345m in 2031-32.

Sources: Budget 2026, overview of tax legislation and rates, paragraph 1.25;
HMRC, "Taxation of company cars: the appropriate percentage for tax years
2030 to 2031 and 2031 to 2032" (28 October 2026).
"""

from policyengine_uk.model_api import Scenario

APPROPRIATE_PERCENTAGE = (
    "gov.hmrc.income_tax.benefits_in_kind.company_car.appropriate_percentage"
)
FROM_2030_31 = "2030-04-06.2100-12-31"

# Each rate is 2029-30's (Finance Act 2025 s. 6) plus one point.
COMPANY_CAR_TAX_RISE_2030 = {
    f"{APPROPRIATE_PERCENTAGE}.zero_emission": {FROM_2030_31: 0.10},
    # 1 to 50 g/km, one rate whatever the electric range.
    **{
        f"{APPROPRIATE_PERCENTAGE}.electric_range[{bracket}].amount": {
            FROM_2030_31: 0.20
        }
        for bracket in range(5)
    },
    # 51-54, 55-59, 60-64, 65-69 and 70-74 g/km.
    f"{APPROPRIATE_PERCENTAGE}.co2_band[0].amount": {FROM_2030_31: 0.21},
    f"{APPROPRIATE_PERCENTAGE}.co2_band[1].amount": {FROM_2030_31: 0.22},
    f"{APPROPRIATE_PERCENTAGE}.co2_band[2].amount": {FROM_2030_31: 0.23},
    f"{APPROPRIATE_PERCENTAGE}.co2_band[3].amount": {FROM_2030_31: 0.24},
    f"{APPROPRIATE_PERCENTAGE}.co2_band[4].amount": {FROM_2030_31: 0.24},
    # 75 g/km, and one point more for each 5 g/km above it.
    f"{APPROPRIATE_PERCENTAGE}.graduated.base_rate": {FROM_2030_31: 0.24},
    f"{APPROPRIATE_PERCENTAGE}.maximum": {FROM_2030_31: 0.40},
}

company_car_tax_rise_2030 = Scenario(parameter_changes=COMPANY_CAR_TAX_RISE_2030)
