# Property wealth components and UK land

The model derives worldwide gross property wealth from six household stock
inputs. The companion [policyengine-uk-data change #543](https://github.com/PolicyEngine/policyengine-uk-data/pull/543)
preserves the seven Wealth and Assets Survey (WAS) round-8 gross-property
terms in those six inputs. The earlier [data change #501](https://github.com/PolicyEngine/policyengine-uk-data/pull/501)
combines second homes and buy-to-let into one other-residential input and
separates property wealth from financial and private-pension wealth.

## Source and input contract

| WAS round-8 source | Saved household input | Coverage |
| --- | --- | --- |
| `DVhValueR8` | `main_residence_value` | Main residence |
| `DVHseValR8_sum` | `other_residential_property_value` | Second UK homes, including holiday homes and time-shares |
| `DVBltValR8_sum` | `other_residential_property_value` | UK residential property let for profit, added to second homes |
| `DVBlDValR8_sum` | `non_residential_property_value` | Other UK buildings |
| `DVLUKValR8_sum` | `owned_land` | Direct UK land-only holdings |
| `DVLOSValR8_sum` | `overseas_property_value` | Overseas land and property, including time-shares |
| `DVOprValR8_sum` | `other_property_value` | Other real estate with unspecified geography and property type |

The data producer combines second homes and buy-to-let before exporting
`other_residential_property_value`. There is no additional buy-to-let model
input to add to an aggregate, benefit-capital list or purchase calculation.
The associated `other_residential_property_secured_debt` likewise combines
their identified secured debt.

The [WAS round-8 derived-variable specification](https://doc.ukdataservice.ac.uk/doc/7215/mrdoc/excel/7215_property_dv_spec_r8.xlsx),
worksheet `DV_Spec_Property_R8`, defines `DVPropertyR8` as the sum of all
seven source terms. This is gross property value. The separate `HpropWR8`
measure deducts mortgage liabilities. The model's gross wealth aggregates
retain this distinction from net benefit-capital valuations.

The data producer must reconcile the seven source terms before imputation,
with documented missing, not-applicable and refusal values handled
consistently and reported separately for complete-case and operational
zero-filled reconciliation. It must also remove a saved `property_wealth`
column, including one inherited from an earlier dataset. A conditioning-total
draw and independently imputed component draws do not have an accounting
identity: the model derives the released total from the saved components.

## Aggregates and land

The formulas under `policyengine_uk/variables/household/wealth/` implement:

```text
residential_property_value = main_residence_value
                           + other_residential_property_value

property_wealth = residential_property_value
                + non_residential_property_value
                + owned_land
                + overseas_property_value
                + other_property_value

total_wealth = property_wealth + corporate_wealth
             + private_pension_wealth + savings

household_land_value = (property_wealth - owned_land
                       - overseas_property_value) * regional_intensity
                      + owned_land
```

Residential property covers the identified domestic residential categories.
Overseas and other-real-estate aggregates do not identify residential
subcomponents. Direct UK land enters worldwide property wealth once and UK
household land once at its full value. Identified overseas land and buildings
contribute to worldwide wealth and contribute zero to UK household land.
`total_wealth` receives all property categories through `property_wealth`;
adding land, overseas or other property separately would duplicate them.

`household_land_value.py` retains the existing regional intensities and the
dwelling-weighted fallback for an unknown region. Unclassified other real
estate uses that regional approximation. Its unknown geography means this
can attribute overseas holdings to UK land. Improved source classification,
or excluding unclassified holdings from the domestic land base, requires a
separate modelling decision.

## Uprating and periods

`overseas_property_value` and `other_property_value` are annual household
stocks, defaulting to zero, with GDP-per-capita uprating. Their variable
definitions use `gov.economic_assumptions.indices.obr.per_capita.gdp` and
their dataset registrations use
`gov.economic_assumptions.yoy_growth.obr.per_capita.gdp` in
`policyengine_uk/data/uprating_indices.yaml`. Both registrations are required:
Core carries situation inputs forward using the variable attribute, while
`policyengine_uk/data/economic_assumptions.py` projects stored dataset inputs
using the YAML map. Stored annual inputs take precedence over formula and
fallback calculations.

Current `main_residence_value` and `other_residential_property_value` use the
model's annual OBR house-price index in both routes. Non-residential property
and direct UK land retain GDP-per-capita uprating. The property-component
change preserves these existing choices; the historical specification's
blanket GDP treatment for residential inputs is obsolete. Each projected
year must retain the aggregate identity using the individually uprated
components, rather than grow a saved property total with a single index.
Monthly requests for these stocks retain the full stock amount rather than
one twelfth of the annual amount.

The upstream regional house-price adjustment to main-residence imputation is
separate from the model's projection indexes. Source reconciliation must
precede that adjustment; the other mapped source categories do not acquire
the adjustment through the aggregate.

## Benefit-capital routing

Countable capital reads configured sources, rather than `property_wealth`.
The new overseas and other-property inputs enter each affected programme's
configured capital sources once and receive the existing real-property
sale-expense treatment. The shared `policyengine_uk/utils/capital_valuation.py` helper
deducts source-specific sale expenses before mapped secured debt, with the
existing zero floor for secured-property categories. A source appearing only
in a sale-expense list does not become countable capital.

Capital parameters are under these paths relative to
`policyengine_uk/parameters/`:

| Programme | Capital directory |
| --- | --- |
| Universal Credit | `gov/dwp/universal_credit/means_test/capital/` |
| Housing Benefit | `gov/dwp/housing_benefit/means_test/capital/` |
| Income Support | `gov/dwp/income_support/means_test/capital/` |
| Income-based JSA | `gov/dwp/JSA/income/capital/` |
| Income-related ESA | `gov/dwp/ESA/income/capital/` |
| Pension Credit | `gov/dwp/pension_credit/income/capital/` |

Universal Credit keeps financial `sources.yaml` separate from
`property_sources.yaml` and `uc_property_capital`. Its existing domestic
property valuation variables remain in that property pool, independent of
financial `benunit_reported_capital` observations. The new overseas and
unclassified other-property categories enter `sources.yaml` and
`sale_expenses/sources.yaml`, so they use the financial proxy pool: a
nonnegative `benunit_reported_capital` observation replaces them, and a report
or complete override reduces the residual pool shared by unreported units.
A complete `uc_reported_capital` override replaces the ordinary assessment
before the existing company-capital substitution. Existing domestic property
shares remain allocated across all claimant/partner adults, with
complete-override units consuming their shares rather than redistributing
them. Direct `owned_land` remains outside UC countable sources; adding it
requires a separate model decision.

The other five programmes retain their existing financial/property source
lists, reported-capital precedence and household-to-benefit-unit allocation
rules. `share_like_capital` retains the component-aware financial fallback,
so the new property sources do not restore `corporate_wealth` lists or add
the underlying share components twice. Main residence and the separately
identified private-pension input remain excluded from countable sources.

These broad asset categories do not identify every statutory disregard or
individual's beneficial ownership. Their allocation is a model assumption,
not an observation of legal ownership or a determination that every holding
is countable. No new secured-debt inputs are exported for overseas or other
real estate, so the mapping cannot identify or deduct debt on those holdings.
Legacy financial aggregates may also contain pension wealth that cannot be
separately identified. Gross worldwide wealth remains distinct from these
limited net capital proxies.

UC unearned income continues to use its claimant unearned-income source
list. Actual interest, dividends and rent are excluded at every capital
level; countable capital affects tariff income. There is no historical
property-income gate to extend.

## Purchases and downstream consumers

Current main uses explicit transaction inputs for
`additional_residential_property_purchased` and
`non_residential_property_purchased`. Holding other-residential or
non-residential stock does not automatically create a purchase when
`property_purchased` is true. This supersedes the historical stock-based
purchase proxy described in the original companion specification. A domestic
additional-dwelling transaction is supplied once, including a buy-to-let
purchase; overseas and unclassified other-property stocks create no UK SDLT
transaction. `main_residential_property_purchased` retains its existing
main-residence-value calculation.

The current consumer paths below replace historical wheel file-and-line
citations. Paths are relative to `policyengine_uk/variables/`.

| Consumer | Current path and dependency |
| --- | --- |
| Residential and worldwide property | `household/wealth/residential_property_value.py` and `property_wealth.py` use the component identities above |
| Total wealth and wealth deciles | `household/wealth/total_wealth.py` includes property once; `household_wealth_decile.py` reads total wealth with person-weighted household weights |
| Wealth taxes | `contrib/ubi_center/wealth_tax.py` reads total wealth; `contrib/cec/non_primary_residence_wealth_tax.py` subtracts main residence from total wealth |
| UK land and LVT | `household/wealth/household_land_value.py` estimates domestic household land; `land_value.py` adds corporate land; `contrib/ubi_center/land_value_tax.py` applies the configured combined, household and corporate rates |
| Domestic property purchases | `household/consumption/main_residential_property_purchased.py`, `additional_residential_property_purchased.py` and `non_residential_property_purchased.py` retain their separate transaction routing |
| SDLT | `gov/hmrc/sdlt_on_residential_property_transactions.py` and `sdlt_on_non_residential_property_transactions.py` read transactions; `stamp_duty_land_tax.py` aggregates liabilities and `expected_sdlt.py` carries the household liability |
| High Value Council Tax Surcharge | `gov/hmrc/high_value_council_tax_surcharge.py` reads main residence and ownership tenure directly |
| Benefit capital | `gov/dwp/universal_credit/uc_assessable_capital.py` and `uc_property_capital.py`; the assessable-capital variables for Housing Benefit, Pension Credit, Income Support, JSA and ESA use the configured programme sources |
| UC unearned income | `gov/dwp/universal_credit/income/uc_unearned_income.py` reads configured claimant income sources, without a property-income gate |

Changing the aggregate alone does not directly change benefit capital,
purchase transactions or the high-value surcharge at fixed inputs and
weights. Completing the missing components and their routing can change
capital; subsequent recalibration can also change weighted outputs.

## Release boundary and validation

The model and the data release carrying the component contract must land in
lockstep, after the data #501 prerequisite. That data release must depend on
a model release with the new inputs and capital-valuation routing. Its
compatibility guard must reject a model unable to carry the new components.

Existing datasets are not migrated. A stored `property_wealth` input remains
authoritative and overrides the formula, even after the model changes. The
new release must stop storing it and remove inherited copies; updating only
the installed model cannot repair old saved totals.

Synthetic tests cover isolated and mixed components, aggregate identities,
land accounting, household LVT, monthly stocks, situation and dataset
uprating, benefit valuation and transaction routing without licensed data.
They do not establish reconciliation of the licensed WAS household source.
The upstream seven-term reconciliation must run on that licensed source
before release, with its missing-value report and the second-home/buy-to-let
combination checked before imputation.

Population and LVT effects remain unmeasured until the compatible data release
exists and is rebuilt and recalibrated. Existing land target definitions and
weights are unchanged, but calculated land, losses and fitted geographic
weights can change. Production rebuilding, recalibration and impact
measurement are separate release work.
