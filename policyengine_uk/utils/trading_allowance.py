"""The trading allowance (ITTOIA 2005 Part 6A Chapter 1), shared by
trading_allowance_deduction and miscellaneous_income_trading_allowance_deduction.

One allowance covers an individual's "relevant income": the receipts of
their relevant trades and their miscellaneous income, which s. 783AB defines
as income chargeable under Part 5 Chapter 8 (income not otherwise charged),
before expenses (ss. 783A and 783AC). Full relief, partial relief and the
opt-out each apply to the relevant income as a whole, so the two deductions
come from one decision.
"""

from policyengine_core.model_api import max_, min_, where

from policyengine_uk.utils.supplied_inputs import supplied_input


def trading_allowance_reliefs(person, period, parameters):
    """The allowance's relief on trades and on miscellaneous income.

    Returns ``(trade_relief, miscellaneous_relief)``: the deduction from
    trading profits beyond the expenses and capital allowances already
    deducted from them, and the deduction from income not otherwise charged.

    - Full relief (s. 783AE(1)): when trade receipts and miscellaneous income
      together are within the allowance, trade profits or losses and the
      miscellaneous income are treated as nil (ss. 783AF and 783AG).
    - Partial relief (ss. 783AH-783AK, on election under s. 783AM): above the
      allowance, each trade's profit is its receipts less its share of the
      allowance, with no expenses, and the miscellaneous income is that
      income less its share. The shares add up to the allowance and the
      individual chooses them (s. 783AK). The model gives the trades their
      receipts' worth first, which keeps Class 4 as low as it can be, so the
      miscellaneous income gets the part of the allowance the trade receipts
      leave. Where trade receipts exceed the allowance it gets none: partial
      relief then beats actual deductions exactly when the trades' expenses
      and capital allowances are under the allowance, and the trades take
      all of it. Every split leaves the same trade and miscellaneous income
      in total, relevant income less the allowance, but two other reliefs
      read the trade's share alone, so a smaller trade share can charge less
      income tax this year:
      - losses brought forward (loss_relief, ITA 2007 s. 83) absorb the
        trade profit it leaves, but that uses up loss which otherwise
        carries forward against later profits of the trade (s. 84);
      - pension contributions above relevant UK earnings (FA 2004 s. 189)
        get more relief, since trade profit counts towards those earnings
        and miscellaneous income does not.
      The model keeps the trades-first split in both cases: it leaves the
      loss for later years and keeps Class 4 profits lower, but it does not
      always minimise the year's income tax and Class 4 together.
    - Ordinary treatment: an individual whose relevant income is within the
      allowance can elect out of full relief (s. 783AL), and one above it
      need not elect for partial relief (s. 783AM). A raw current trading
      loss larger than the saving from both deductions is claimed instead,
      and then neither applies.

    Without gross receipts, a trade's receipts are taken as the lowest its
    profit allows: a profit within the allowance is taken as receipts equal
    to the profit, which takes up that much of the allowance, and a loss or
    no profit as no receipts, which leaves all of it for miscellaneous
    income. A larger profit is taken to reflect the better of actual
    expenses and the allowance already, which leaves none of it.

    The miscellaneous income is income_not_otherwise_charged, up to the
    person's miscellaneous_income when that is positive (it is part of it).
    The model holds no expenses against it. Not modelled: the exclusions in
    ss. 783AN-783AQ (rent-a-room receipts, and income including a payment
    from the person's employer, firm or close company), and a loss created
    by capital allowances, which the model never sets against other income.
    """
    allowance = parameters(period).gov.hmrc.income_tax.allowances.trading_allowance
    profit = person("self_employment_income", period)
    receipts = person("self_employment_gross_receipts", period)
    capital_allowances = person("capital_allowances", period)
    # Receipts below profit (including the default zero) mean unknown.
    receipts_known = (receipts > 0) & (receipts >= profit)
    expenses = max_(receipts - profit, 0)
    # Full relief (receipts within the allowance, s. 783AE-783AF) makes
    # the profit nil; partial relief (s. 783AI) replaces expenses and
    # capital allowances with the allowance. Both come to the allowance's
    # excess over actual deductions, capped at profit.
    relief_with_receipts = min_(profit, allowance - expenses) - capital_allowances
    relief_without_receipts = where(profit <= allowance, profit - capital_allowances, 0)
    trade_relief = where(receipts_known, relief_with_receipts, relief_without_receipts)
    trade_relief = max_(trade_relief, 0)

    # The trade receipts that use the allowance first. Unknown receipts are
    # the profit within the allowance, and otherwise use all of it.
    trade_receipts = where(
        receipts_known,
        receipts,
        where(profit <= allowance, max_(profit, 0), allowance),
    )
    miscellaneous_income = min_(
        max_(person("income_not_otherwise_charged", period), 0),
        max_(person("miscellaneous_income", period), 0),
    )
    miscellaneous_relief = min_(
        miscellaneous_income, max_(allowance - trade_receipts, 0)
    )

    # Full relief makes every relevant trade's current profit AND loss
    # nil (s.783AF); the election out of it (s.783AL), like not electing for
    # partial relief (s.783AM), is for the individual/year and takes the
    # miscellaneous income's relief with it. Partial relief also
    # replaces every trade's actual expenses. Choose ordinary treatment if
    # the raw supplied current loss exceeds the allowance saving. Before
    # applying net-income and relief-cap limits, this also preserves an
    # unused loss if both choices give nil income. Prior s.83 losses remain
    # separate and may follow partial relief.
    profit_after_other_deductions = max_(
        0, profit - capital_allowances - person("loss_relief", period)
    )
    allowance_saving = (
        min_(trade_relief, profit_after_other_deductions) + miscellaneous_relief
    )
    # An earlier input carried/uprated into this year is not a new loss
    # for the election, just as it is not a new Class 4 loss.
    current_loss = supplied_input(person, "trading_loss", period)
    if current_loss is None:
        current_loss = person.empty_array()
    claim_current_loss = current_loss > allowance_saving
    return (
        where(claim_current_loss, 0, trade_relief),
        where(claim_current_loss, 0, miscellaneous_relief),
    )
