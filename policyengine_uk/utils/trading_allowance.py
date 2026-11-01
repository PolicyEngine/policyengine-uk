"""The trading allowance (ITTOIA 2005 Part 6A Chapter 1), shared by
trading_allowance_deduction and miscellaneous_income_trading_allowance_deduction.

One allowance covers an individual's "relevant income": the receipts of
their relevant trades and their miscellaneous income, which s. 783AB defines
as income chargeable under Part 5 Chapter 8 (income not otherwise charged),
before expenses (ss. 783A and 783AC). Full relief, partial relief and the
opt-out each apply to the relevant income as a whole, so the two deductions
come from one decision.
"""

from policyengine_core.model_api import max_, min_, round_, where

from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.supplied_inputs import (
    supplied_input,
    supplied_input_periods,
)


def _data_year(person, period):
    """The year the input self-employment profit was measured.

    - A UK dataset: its first year, which the engine projects to later
      years, as the State Pension variables read it. Its inputs are stored
      for every projected year, so the years they were supplied for say
      nothing here.
    - Other data without years, such as a policyengine-core Dataset: the
      earliest year self_employment_income was supplied for, for the same
      reason.
    - A situation: the latest year, up to the one simulated, for which the
      situation gave self_employment_income, as recorded when it was built
      (Simulation.build_from_situation), so that a later write of the
      profit, by a scenario's modifier or a derivative, does not move it. A
      profit carried from an earlier year keeps that year's allowance: a
      2025-26 profit simulated in 2027-28 deducted £1,000, and gains from
      the raise to £3,000. The builder stores a year's inputs for everyone
      in the situation, giving anyone not set the default, so one year
      serves them all. A simulation built some other way reads the profit's
      supplied years as they stand.
    With no profit supplied, the year simulated.

    Not handled: data cannot declare the year their incomes were measured
    in, so a file saved from a later projected year, or a situation saved
    over several years, is read as measured in its first year.
    """
    from policyengine_uk.data import UKMultiYearDataset

    simulation = person.simulation
    if built_from_data(simulation):
        # Checked by type: a policyengine-core Dataset loads any attribute
        # it is asked for as a table, so it cannot be asked for years.
        dataset = getattr(simulation, "dataset", None)
        if isinstance(dataset, UKMultiYearDataset):
            return min(dataset.years)
        supplied = supplied_input_periods(person, "self_employment_income")
        return (supplied[0] if supplied else period).start.year
    years = getattr(simulation, "_situation_profit_years", None)
    if years is None:
        years = [
            supplied_period.start.year
            for supplied_period in supplied_input_periods(
                person, "self_employment_income"
            )
        ]
    earlier = [year for year in years if year <= period.start.year]
    return earlier[-1] if earlier else period.start.year


def trading_allowance_reliefs(person, period, parameters):
    """The allowance's relief on trades and on miscellaneous income.

    Returns ``(trade_relief, miscellaneous_relief, claimant_takes_allowance)``:
    the deduction from trading profits beyond the expenses and capital
    allowances already deducted from them, the deduction from income not
    otherwise charged, and whether a claimant (below) takes the allowance.

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

    trading_allowance_claim_status says which receipts lie behind a positive
    profit. A person with no profit has no trade receipts for it to
    describe, and a claimant is then read as unknown.
    - A claimant's profit is their receipts less the allowance legislated
      for the year the profit was measured (the input allowance, see
      _data_year), which reforms do not move. Their claim was an election
      for partial relief (s. 783AM), which replaced their expenses and
      capital allowances (s. 783AI): capital_allowances supplied for them
      are not deducted, and their receipts, profit plus the input
      allowance, take precedence over gross receipts. Their actual expenses
      and capital allowances are below the input allowance but unknown:
      gov.simulation.trading_allowance_claimant_expense_share of it, between
      0 and 1 and by default all of it, in pennies, or the capital
      allowances supplied for them where those are larger. Their options
      are the allowance, which leaves receipts less the allowance (nil
      within it), and ordinary treatment, which leaves receipts less those
      expenses and lets a supplied current loss be claimed. They make the
      same election as everyone else: the allowance, if it covers their
      expenses and its saving over them is at least such a loss. (Covering
      them matters where losses brought forward absorb both options: the
      saving then ties at nil, and the allowance below their expenses would
      charge Class 4, which does not see those losses, more.) So under the
      default share a claimant with no loss keeps the allowance at or above
      the input allowance, where the deduction is its excess over the input
      allowance, capped at profit, and a cut leaves their profit as
      reported, the lower bound of its yield; a claimant with a loss claims
      it until the allowance saves more. The tax they pay never jumps as
      the allowance or the loss moves. The deduction is negative where it
      gives back capital allowances or charges what a cut adds. Their
      receipts take up the allowance before income not otherwise charged,
      as other receipts do.
    - A non-claimant does not elect for partial relief, which would be a
      change in behaviour after a raise, so takes ordinary treatment unless
      their relevant income is within the allowance: full relief needs no
      election (s. 783AE). Their receipts exceed their profit plus the input
      allowance and are unknown unless supplied, so only supplied receipts,
      or casual income alone where there is no profit, can show that.

    The miscellaneous income is income_not_otherwise_charged, up to the
    person's miscellaneous_income when that is positive (it is part of it).
    The model holds no expenses against it. Not modelled: the exclusions in
    ss. 783AN-783AQ (rent-a-room receipts, and income including a payment
    from the person's employer, firm or close company), and a loss created
    by capital allowances, which the model never sets against other income.
    """
    p = parameters(period)
    allowance = p.gov.hmrc.income_tax.allowances.trading_allowance
    # The baseline tree is the legislated one, which reforms leave alone. It
    # is not annualised, so it is read on 30 April, where the fiscal-year
    # conversion samples the gov tree.
    input_allowance = parameters(
        f"{_data_year(person, period)}-04-30"
    ).baseline.gov.hmrc.income_tax.allowances.trading_allowance
    status = person("trading_allowance_claim_status", period)
    profit = person("self_employment_income", period)
    receipts = person("self_employment_gross_receipts", period)
    capital_allowances = person("capital_allowances", period)
    # A claimant's actual expenses and capital allowances: the share of the
    # input allowance, in pennies, or the capital allowances supplied for
    # them where those are larger, but never above the allowance they chose
    # instead.
    expense_share = p.gov.simulation.trading_allowance_claimant_expense_share
    # A claimant's figures are all in float64, so that the two options tie
    # exactly where the allowance equals their expenses.
    claimant_profit = profit.astype(float)
    claimant_capital_allowances = capital_allowances.astype(float)
    claimant_expenses = min_(
        max_(
            round_(min_(max_(expense_share, 0), 1) * input_allowance, 2),
            round_(claimant_capital_allowances, 2),
        ),
        input_allowance,
    )
    trading = profit > 0
    claimant = trading & (status == status.possible_values.CLAIMANT)
    non_claimant = status == status.possible_values.NON_CLAIMANT

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
    # A claimant's receipts are their profit plus the input allowance. Their
    # options are the allowance, which leaves receipts less the allowance,
    # nil within it, and ordinary treatment, which leaves receipts less their
    # expenses. Each deduction is from the profit and gives back the capital
    # allowances deducted separately, which either option replaces.
    claimant_allowance_relief = (
        min_(claimant_profit, allowance - input_allowance) - claimant_capital_allowances
    )
    claimant_ordinary_relief = (
        min_(claimant_profit, claimant_expenses - input_allowance)
        - claimant_capital_allowances
    )
    trade_receipts = where(claimant, profit + input_allowance, trade_receipts)

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
    loss_relief = person("loss_relief", period)
    profit_after_other_deductions = max_(0, profit - capital_allowances - loss_relief)
    allowance_saving = (
        min_(trade_relief, profit_after_other_deductions) + miscellaneous_relief
    )
    # A claimant's saving is the allowance's over their own ordinary
    # treatment, after losses brought forward.
    claimant_before_relief = (
        claimant_profit - claimant_capital_allowances - loss_relief.astype(float)
    )
    claimant_saving = (
        max_(claimant_before_relief - claimant_ordinary_relief, 0)
        - max_(claimant_before_relief - claimant_allowance_relief, 0)
        + miscellaneous_relief
    )
    # An earlier input carried/uprated into this year is not a new loss
    # for the election, just as it is not a new Class 4 loss.
    current_loss = supplied_input(person, "trading_loss", period)
    if current_loss is None:
        current_loss = person.empty_array()
    # A non-claimant gets the allowance only through full relief, where
    # supplied receipts, or casual income alone with no profit, show
    # relevant income within it.
    within_allowance = where(
        receipts_known,
        receipts + miscellaneous_income <= allowance,
        ~trading & (miscellaneous_income <= allowance),
    )
    ordinary = (non_claimant & ~within_allowance) | (current_loss > allowance_saving)
    # A claimant makes the same election against their own options: the
    # allowance unless it does worse than their expenses, or than a larger
    # supplied current loss. Ties take the allowance.
    # The allowance must also cover their expenses: where losses brought
    # forward absorb both options the saving ties at nil, and the allowance
    # would then charge Class 4, which does not see those losses, more.
    claimant_takes_allowance = (
        claimant
        & (allowance > 0)
        & (allowance >= claimant_expenses)
        & ~(current_loss > claimant_saving)
    )
    return (
        where(
            claimant,
            where(
                claimant_takes_allowance,
                claimant_allowance_relief,
                claimant_ordinary_relief,
            ),
            where(ordinary, 0, trade_relief),
        ),
        where(
            claimant,
            where(claimant_takes_allowance, miscellaneous_relief, 0),
            where(ordinary, 0, miscellaneous_relief),
        ),
        claimant_takes_allowance,
    )
