"""The rate test for the Marriage Allowance (ITA 2007 s. 55B(2)(b) and (ba)).

The test reads the income the reliefs and allowances leave in each component,
so it depends on how s. 25(2) shares them.
``meets_marriage_allowance_income_conditions`` applies it to the share the
model settles on, and ``income_tax_allocation`` to each share it compares.
"""

from types import SimpleNamespace

import numpy as np


def marriage_allowance_rate_limits(person, period, income_tax):
    """The limits the rate test applies for the tax year.

    Parliament extends the rate limits by the grossed-up Gift Aid gift
    (s. 414(2)(b)); the gift does not reduce taxable income. Before 2017-18
    this test uses the basic rate limit for Scottish taxpayers, even though
    the model's historical Scottish liability currently reads the 2017-18
    schedule.
    """
    rates = income_tax.rates
    gross_gift = person("gift_aid_grossed_up", period)
    # The Scottish higher rate follows the starter, basic and intermediate
    # rates; in 2017-18 the Scottish scale had only the basic rate below it.
    # Before 2017-18 the test holds a Scottish taxpayer to the basic rate
    # limit. The Scottish rates of s. 11A start in 2016-17 (FA 2014 Sch. 38
    # para. 12, SI 2015/2000 art. 3). That year Parliament charged the Scottish
    # basic rate on income that would otherwise bear the basic rate
    # (s. 11A(1)). The model reads its Scottish scale's 2017-18 values in
    # earlier years too, so the test sets the limit by the year.
    scottish = rates.scotland.rates
    basic_rate_limit = rates.uk.thresholds[1] + gross_gift
    if period.start.year < 2017 or len(scottish.rates) < 3:
        scottish_limit = basic_rate_limit
    elif len(scottish.rates) == 3:
        scottish_limit = scottish.thresholds[1] + gross_gift
    else:
        scottish_limit = scottish.thresholds[3] + gross_gift
    non_savings_limit = np.where(
        person("pays_scottish_income_tax", period),
        scottish_limit,
        basic_rate_limit,
    )
    # Parliament gave the savings nil rate effect from 2016-17 (FA 2016
    # s. 4(17)).
    if period.start.year < 2016:
        savings_allowance = 0
    else:
        savings_allowance = person("savings_allowance", period)
    return SimpleNamespace(
        non_savings=non_savings_limit,
        basic_rate=basic_rate_limit,
        starting=rates.savings_starter_rate.allowance,
        savings_allowance=savings_allowance,
    )


def meets_marriage_allowance_rate_test(non_savings, savings, dividends, limits):
    """Whether non-savings income, savings and dividends left after the
    deductions bear only the rates Parliament permits (s. 55B(2)(b) and (ba)),
    against ``marriage_allowance_rate_limits``."""
    # Savings sit above non-savings income (s. 16) and take the rest-of-UK
    # limits (s. 11D(6)). Up to the basic rate limit they bear a basic rate or
    # the starting rate for savings, both permitted: Parliament charges the
    # starting rate only on savings that would otherwise bear a basic rate
    # (s. 12(1), and s. 12(1)(b) from 2017-18). Above the limit it permits only
    # the savings nil rate (s. 55B(2)(b)), which it charges on the lowest
    # savings above the starting rate limit for savings, up to the savings
    # allowance (s. 12A(1) to (4)); dividends sit above savings (s. 16) and
    # don't move this slice. The person fails the test if any savings above the
    # basic rate limit lie outside the slice.
    below_dividends = non_savings + savings
    nil_rate_start = np.maximum(non_savings, limits.starting)
    nil_rate_top = np.minimum(
        below_dividends, nil_rate_start + limits.savings_allowance
    )
    savings_above_basic = np.maximum(
        0, below_dividends - np.maximum(non_savings, limits.basic_rate)
    )
    nil_rate_above_basic = np.maximum(
        0, nil_rate_top - np.maximum(nil_rate_start, limits.basic_rate)
    )
    savings_at_forbidden_rates = savings_above_basic - nil_rate_above_basic > 0
    # Dividends form the top slice, above all non-savings income and savings
    # (s. 16); count them before the dividend allowance. Parliament charges the
    # dividend upper rate on dividends that would otherwise bear the higher
    # rate (s. 13(2)), and the higher rate starts at the basic rate limit plus
    # the gross gift (ss. 10(3) and 414(2)(b)).
    dividends_above_basic = (dividends > 0) & (
        below_dividends + dividends > limits.basic_rate
    )
    return (
        (non_savings <= limits.non_savings)
        & ~savings_at_forbidden_rates
        & ~dividends_above_basic
    )
