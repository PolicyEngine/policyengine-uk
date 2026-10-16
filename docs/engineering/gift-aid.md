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

Savings and dividends stack above all non-savings income, property income
included ([ITA 2007 s. 16](https://www.legislation.gov.uk/ukpga/2007/3/section/16);
#2352). Property income, savings and dividends therefore fill the bands in that
order, each against the extended limits. Property income is taxed on top of
`non_savings_income_after_allowances` less property income after allowances,
and savings and dividends on top of `non_savings_taxable_income`
(`earned_taxable_income` plus property income after allowances). Both bases
derive from `net_income`, so the gift raises the limits without also shrinking
the income beneath them. They differ only when Marriage Allowance applies,
which `earned_taxable_income` subtracts (#1947). The Personal Savings Allowance
compares net income less allowances with the UK basic and higher rate limits,
both extended by the gross gift ([s. 12B](https://www.legislation.gov.uk/ukpga/2007/3/section/12B),
including s. 12B(8) for Scottish taxpayers, with s. 414(2)(b)).

## Existing limitations

Zero-gift calculations retain their existing behavior. Several inherited
limitations remain relevant when interpreting mixed-income results:

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

## Pension annual allowance charge

The annual allowance charge uses reduced net income after ITA 2007 s. 23
Step 3 ([FA 2004 s. 227(4B)](https://www.legislation.gov.uk/ukpga/2004/12/section/227)).
It starts from `net_income`, before the s. 58 gross Gift Aid deduction, and
subtracts `allowances` after removing relieved relief-at-source pension
contributions. Gift Aid is already excluded from those allowances. The charge
then stacks the excess pension input amount on this base. Gross Gift Aid
extends the rate limits under s. 227(4C), independently of pension relief.
This keeps the Gift Aid adjustment to adjusted net income separate from the
amount charged to tax.

The pension extension is conditional. [FA 2004 s. 192(4)/(4A)](https://www.legislation.gov.uk/ukpga/2004/12/section/192)
requires ordinary income, apart from relief under that section, to attract
higher/additional-rate tax, or a Scottish rate above basic. The charge uses
only limits increased under s. 192; s. 227(5) excludes the pension excess from
income, so that excess cannot satisfy the condition. The model tests ordinary
liability before RAS relief, retaining Gift Aid's extension and the existing
allowance allocation. Scottish liability uses non-savings income; dividend
rates alone and savings taxed at nil do not satisfy the UK condition.

[HMRC PTM056120](https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm056120)
describes the RAS extension for the annual allowance charge without stating
this condition. Its examples do not resolve low-income contributors whose
pension excess crosses a band. The model follows the statutory condition;
the [2018/459 explanatory memorandum, paragraph 7.4](https://www.legislation.gov.uk/uksi/2018/459/pdfs/uksiem_20180459_en.pdf)
also describes an above-basic Scottish liability requirement. Assessment
practice under the broader manual description remains a methodology question.
The charge can exceed relief on the contribution when ordinary income fails
the condition, so contribution and Gift Aid tax-monotonicity comparisons must
hold eligibility for the RAS extension fixed.
