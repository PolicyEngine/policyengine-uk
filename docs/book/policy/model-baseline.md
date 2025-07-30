# Model baseline

PolicyEngine UK models the UK tax and benefit system as of 2025, incorporating major reforms from 2020-2025. This page documents the key policy changes by year, working backwards from 2025, showing how each reform is implemented in the codebase.

## 2025 reforms

### Autumn Budget 2024

The government increased the [employer National Insurance rate from 13.8% to 15%](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/national_insurance/class_1/rates/employer.yaml#L13-L17) and reduced the [employer secondary threshold from £9,100 to £5,000 annually](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/national_insurance/class_1/thresholds/secondary_threshold.yaml#L26-L30), both taking effect in fiscal year 2025-26.

### Universal Credit rebalancing

Parliament passed legislation to implement Universal Credit rebalancing reforms, with the [rebalancing switch activated in fiscal year 2025-26](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/dwp/universal_credit/rebalancing/active.yaml#L3). The reforms include [graduated standard allowance uplifts](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/dwp/universal_credit/rebalancing/standard_allowance_uplift.yaml) above inflation: 2.3% in 2026-27, 3.1% in 2027-28, 4.0% in 2028-29, and 4.8% in 2029-30. A [new health element of £217.26](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/dwp/universal_credit/rebalancing/new_claimant_health_element.yaml#L3) will be introduced for new claimants in fiscal year 2026-27.

### Benefit uprating

Annual benefit uprating applied 4.1% increases to state pensions and 1.7% to working-age benefits, implemented through the [standard uprating mechanism](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/benefit_uprating_cpi.yaml).

## 2024 reforms

### Autumn Statement 2023

The government announced further National Insurance cuts, reducing the [employee main rate from 10% to 8%](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/national_insurance/class_1/rates/employee/main.yaml#L22-L27) and the [self-employed Class 4 rate from 9% to 6%](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/national_insurance/class_4/rates/main.yaml#L16-L21) in fiscal year 2024-25. [Class 2 National Insurance contributions were abolished](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/national_insurance/class_2/flat_rate.yaml#L14-L19) for self-employed people, with the flat rate set to £0 in fiscal year 2024-25.

### Capital gains tax changes (Autumn Budget 2024)

The government increased capital gains tax rates from 10%/20% to [18% for basic rate taxpayers](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/cgt/basic_rate.yaml#L4) and [24% for higher rate taxpayers](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/cgt/higher_rate.yaml#L4) in fiscal year 2025-26.

### Spring Budget 2024

The government increased the [child benefit high income tax charge threshold from £50,000 to £60,000](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/income_tax/charges/CB_HITC/phase_out_start.yaml#L4) in fiscal year 2024-25.

### Autumn Statement 2023 (Employee NI cut)

An initial National Insurance cut reduced the [employee main rate from 12% to 10%](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/national_insurance/class_1/rates/employee/main.yaml#L16-L21) in fiscal year 2024-25.

## 2023 reforms

### Autumn Statement 2022

The government reduced the [additional rate income tax threshold from £150,000 to £125,140](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/income_tax/rates/uk.yaml#L74-L78), taking effect in fiscal year 2023-24. The government also began reducing the [capital gains tax annual exempt amount from £12,300 to £6,000](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/cgt/annual_exempt_amount.yaml#L6-L10) in fiscal year 2023-24, with a further reduction to [£3,000 in fiscal year 2024-25](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/cgt/annual_exempt_amount.yaml#L11-L15).

## 2022 reforms

### Spring Statement 2022

The government announced an increase in the [National Insurance primary threshold from £9,880 to £12,570](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/national_insurance/class_1/thresholds/primary_threshold.yaml#L17-L22), aligning it with the personal allowance in fiscal year 2022-23.

### Autumn Budget 2021 (Health and Social Care Levy)

The government temporarily increased [National Insurance rates by 1.25 percentage points](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/national_insurance/class_1/rates/employee/main.yaml#L4-L10) in fiscal year 2022-23, later reversed the same fiscal year.

### Mini-Budget 2022 (September)

The government announced increases to [stamp duty nil rate thresholds](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/stamp_duty/residential/purchase/main/subsequent.yaml), raising the main threshold from £125,000 to £250,000 and the first-time buyer threshold to £425,000.

### Cost of living support

The government announced cost of living payments: [£650 for means-tested benefit recipients](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/treasury/cost_of_living_support/means_tested_households/amount.yaml#L3), [£300 for pensioners](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/treasury/cost_of_living_support/pensioners/amount.yaml#L3), and [£150 for disability benefit recipients](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/treasury/cost_of_living_support/disabled/amount.yaml#L3), implemented through dedicated [payment calculation variables](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/variables/gov/treasury/cost_of_living_support/cost_of_living_support_payment.py).

### Energy Price Guarantee

Following the energy crisis, the government introduced an [Energy Price Guarantee capping typical household bills at £2,500](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/ofgem/energy_price_guarantee.yaml#L12-L18) in fiscal year 2022-23.

## 2021 reforms

### Autumn Budget 2021

The government reduced the [Universal Credit taper rate from 63% to 55%](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/dwp/universal_credit/means_test/reduction_rate.yaml#L5) and increased [work allowances by £500 annually](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/dwp/universal_credit/means_test/work_allowance/without_housing.yaml#L9) in fiscal year 2021-22.

### End of COVID-19 support

The government ended the [Universal Credit £20 weekly uplift](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/dwp/universal_credit/standard_allowance/amount.yaml) in fiscal year 2021-22, with rates reducing from the elevated 2020-21 levels.

### Stamp duty holiday extension

The government extended the stamp duty holiday with [phased withdrawal of the nil rate increases](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/stamp_duty/residential/purchase/main/subsequent.yaml#L20-L22) during fiscal year 2021-22.

## 2020 reforms

### Summer Economic Update (July 2020)

The government introduced a [stamp duty holiday with nil rates up to £500,000](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/hmrc/stamp_duty/residential/purchase/main/subsequent.yaml#L9-L15) in fiscal year 2020-21 to support the housing market.

### COVID-19 response (March 2020)

Emergency measures included a [£20 weekly increase to Universal Credit standard allowances](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/parameters/gov/dwp/universal_credit/standard_allowance/amount.yaml#L6) and other working-age benefits in fiscal year 2020-21.

## Current baseline (2025)

The model baseline includes all reforms above, resulting in:
- **Income tax**: 20%/40%/45% rates with personal allowance of £12,570 and higher rate threshold of £50,270
- **National Insurance**: 8% employee rate, 15% employer rate, 6% self-employed rate
- **Capital gains tax**: 18%/24% rates with £3,000 annual exempt amount
- **Universal Credit**: 55% taper rate with rebalancing reforms active
- **Benefits**: Standard uprating with targeted cost of living support for 2022

## What is not modelled

The model does not include:
- **PIP reform announced in Autumn Statement 2023**: The government announced reforms to Personal Independence Payment assessments and eligibility criteria, phasing out 25% of claimants between 2025-29. These reforms are [defined as a scenario](https://github.com/PolicyEngine/policyengine-uk/blob/master/policyengine_uk/scenarios/pip_reform.py) but not included in the baseline model
- **Non-domiciled taxation changes**: Remittance basis abolition and four-year exemption regime from fiscal year 2025-26 are not modelled
- **Non-UK resident stamp duty surcharge**: 2% additional rate from fiscal year 2021-22 is not modelled
- **Some devolved tax policies**: Beyond property transaction taxes, other devolved policies may have limited coverage

All parameter values include references to primary legislation and can be found in the [PolicyEngine UK parameters directory](https://github.com/PolicyEngine/policyengine-uk/tree/master/policyengine_uk/parameters).