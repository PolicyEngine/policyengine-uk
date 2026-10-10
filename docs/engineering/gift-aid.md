# Gift Aid and income tax

`gift_aid` is the net eligible donation. [Income Tax Act 2007
s. 414(2)(a)](https://www.legislation.gov.uk/ukpga/2007/3/section/414)
treats the gift as made after deduction of basic-rate income tax, and
[s. 415](https://www.legislation.gov.uk/ukpga/2007/3/section/415) defines its
grossed-up amount. The model calculates `gift_aid_grossed_up` as the net gift
divided by one minus the UK basic rate.

Gift Aid does not belong in `allowances` and does not reduce taxable income.
Under s. 414(2)(b), the gross gift increases both UK rate limits. For Scottish
non-savings income, it also increases the Scottish basic-rate upper limit and
every limit above it; the starter-rate upper limit remains unchanged. Savings
and dividends use the extended UK limits for Scottish taxpayers too.

The model extends limits where band amounts are calculated. For variables that
use a complete rate scale, `calc_income_tax_with_gift_aid` in
`policyengine_uk/utils/income_tax.py` applies an equivalent correction to the
scale's original calculation. At each extended threshold, it subtracts the
rate increase multiplied by the income between the old and extended limits.
For a stacked slice, subtracting the corrected tax at its bottom from the
corrected tax at its top gives the tax on that slice. This preserves the
original scale calculation when the gift is zero and handles gifts that cross
several thresholds.

`net_income` holds the income base previously exposed as `adjusted_net_income`.
Taxable-income calculations and allowance allocation use this base.
When adjusted net income is supplied explicitly, its gross Gift Aid adjustment
is added back to obtain the taxable-income base. This preserves direct income
inputs when the gift is zero without recovering ordinary taxable income from a
rounded adjusted-net-income calculation. The marriage-neutral income-tax
reform splits `net_income` before each person's Gift Aid adjustment.
`adjusted_net_income` deducts the gross gift once, as [s. 58(1), Step
2](https://www.legislation.gov.uk/ukpga/2007/3/section/58) requires. The Personal
Allowance taper and High Income Child Benefit Charge therefore see the lower
adjusted net income. The Personal Allowance formula does not deduct Gift Aid a
second time. Capital gains tax uses `net_income`, retains its gross Gift Aid
band extension, and no longer removes the net gift from `allowances`.

## Existing limitations

Zero-gift calculations retain their existing behavior. Several inherited
limitations remain relevant when interpreting mixed-income results:

- Savings and dividend stacking currently omits property income from the
  income beneath those slices. Gift Aid extends the limits of those existing
  stacks. [ITA 2007 s. 16](https://www.legislation.gov.uk/ukpga/2007/3/section/16)
  requires savings and dividends above other income; repairing property
  occupancy separately would also change zero-gift results.
- The Personal Savings Allowance follows the model's `tax_band` enum, including
  its Scottish band classification. [s. 12B(8)](https://www.legislation.gov.uk/ukpga/2007/3/section/12B)
  instead tests Scottish non-savings income against the counterfactual UK
  higher and additional rates. Extending the existing band tests preserves
  that limitation.
- The Scottish top-rate threshold parameter is £112,570 of income after
  allowances for 2024 onwards. The [HMRC rates and allowances
  table](https://www.gov.uk/government/publications/rates-and-allowances-income-tax/income-tax-rates-and-allowances-current-and-past)
  gives £125,140 after allowances. The Gift Aid correction extends the model's
  existing threshold and does not repair it.
- Adjusted net income still omits other adjustments in s. 58, including the
  deduction for pension contributions relieved at source in Step 3.
- Gifts are assumed to qualify. The model does not charge the donor for a
  shortfall in income tax and capital gains tax covering the tax attributed to
  gifts under [ss. 423–424](https://www.legislation.gov.uk/ukpga/2007/3/section/424).

## Relief bounds in tests

For a fixed taxable-income stack and fixed zero-rate allowances, the maximum
band-extension relief is the gross gift multiplied by the sum of positive
rate increases at extended limits. For earned income, that cumulative rate
increase is the top rate minus the basic rate: 25 percentage points for the UK
schedule and 28 for the current Scottish schedule. A bound using only the
largest adjacent rate increase would fail even for the £150,000 UK example,
where both UK limits move.

Restoring Personal Allowance through the adjusted-net-income taper can give
additional relief. Changing tax band can also increase the Personal Savings
Allowance discretely under s. 12B, so its relief cannot be bounded by a constant
times a very small gift. Tests of the continuous band-extension bound must
allow for that allowance change or hold the zero-rate allowance fixed.
