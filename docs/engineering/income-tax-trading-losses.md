# Income Tax trading losses

Supply `trading_loss` as the positive loss made in each tax year. Income Tax
recognises only a value explicitly supplied for that year as a current loss;
an earlier value inherited or uprated by the engine is not a new loss.

The existing general-income formula assumes a commercial trade and a claim
against the loss-making year's income under ITA 2007 section 64. It retains
the trading-allowance election, available-income limit and section 24A cap.
It does not choose a previous-year claim or optimise claim ordering.
The available-income limit subtracts the existing ordinary net-pay pension
relief, which is already deducted at Step 1 and cannot also consume a loss
at Step 2. This does not establish the ordering of claimed excess employee
contributions or other pension reliefs.

`loss_relief` is the opening unrelieved Income Tax loss stock. The model assumes
an eligible carry-forward claim under sections 83 and 84 for the same
continuing trade, or a trade pool whose eligibility the caller has assessed.
It does not reconstruct unrelated trades or establish their eligibility from
the person's aggregate profit and loss inputs.

The opening stock for a year follows the actual supplied loss history. Each
earlier year consumes only the stock absorbed by that year's trading profits,
after capital allowances and the trading allowance. Only the year's eligible
new loss left after actual general-income relief enters the next balance.
Relief consumption is the amount deducted from income, rather than the tax
saving. An allowance year can leave an older loss unused. A stock may appear
in several zero-profit years without being deducted in any of them.

An explicit `loss_relief` input, including zero, overrides that year's opening
stock and starts a new accounting segment. Use it to reconcile earlier
history or relief obtained outside the model, including other Income Tax or
capital-gains claims. Do not enter a loss again merely because it remains
unused. The stock can exceed the current deduction: taxable trading profits
remain floored at zero, and brought-forward losses do not reduce other income.

The annual formula resolves past opening balances in ascending order before
requesting each year's allowance and general-income relief. It uses ordinary
engine calculation caching and the existing supplied-input API, without
writing inputs or private caches. The pension annual-allowance net-pay
recomputation also recognises only the exact supplied current loss; its other
pension rules are unchanged.

Class 4 National Insurance keeps its independent balance. A loss used against
pay for Income Tax can still remain available against later Class 4 profits.
Other programmes retain their own loss rules; callers should still supply
later zeros where those programmes read an inherited `trading_loss` value.

These conventions do not implement every historical, early-year, terminal,
foreign-trade, partnership or external-relief election. They do not establish
national impacts, input coverage or population accuracy.

References: [ITA 2007 sections 63–65](https://www.legislation.gov.uk/ukpga/2007/3/part/4/chapter/2),
[sections 83–84](https://www.legislation.gov.uk/ukpga/2007/3/part/4/chapter/2/crossheading/carryforward-trade-loss-relief),
and [section 24A](https://www.legislation.gov.uk/ukpga/2007/3/section/24A).

## A new loss alongside profits

The automatic carry-forward uses aggregate person inputs and does not identify trades. In every year, the caller must establish that each brought-forward loss used by the calculation is deductible from the supplied profits of that same trade, including the required ordering. The aggregate deduction must equal the sum of the permitted same-trade deductions. Supplying a pool does not establish that unrelated losses and profits are compatible.

For example, an old £10,000 loss from trade A in 2025, followed by £8,000 profit from A and a new £4,000 loss from B in 2026, uses £8,000 of A's old stock first. With no other income, ordinary expenses rather than the trading allowance, no pensions, capital allowances or external relief, and eligible current-year claims, current general-income relief is £0. The 2027 opening inventory is £2,000 from A plus £4,000 from B, or £6,000. This balance does not authorise relief against arbitrary later profits: compatibility must be assessed again each year.

If instead both the old and new losses belong to A while the £8,000 profit belongs to B, section 83 cannot deduct A's old stock from B's profit. Under the retained current-year section 64 convention, £4,000 of the current loss can be used, leaving £4,000 net income before personal allowances and £10,000 old stock unrelieved. These identical aggregate inputs do not identify that association, so this case is outside automatic reconstruction. Keep per-trade records externally and supply reconciled annual inputs and balances, or exclude the situation from the automatic calculation. An explicit `loss_relief: 0` resets the accounting segment; it does not suspend an old loss in a hidden ledger. Excluded stock must be explicitly reseeded when appropriate later, accounting for relief already obtained.

## Projected dataset inputs

If a data producer copies a supplied `trading_loss` value into later years, each physical annual input is treated as a new loss for that year. Preserve the original supplied year of a one-off loss and use assessed later inputs, including explicit zeros where appropriate; do not forward-fill it because it remains unused. Copying `loss_relief` likewise supplies a new opening-balance override each year. This conditional input-contract warning makes no claim about current certified-data columns, population coverage or national effects.
