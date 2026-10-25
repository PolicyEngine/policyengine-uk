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
