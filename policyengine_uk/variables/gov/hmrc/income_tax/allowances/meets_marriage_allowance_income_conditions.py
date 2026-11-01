from policyengine_uk.model_api import *


def liable_only_at_marriage_allowance_rates(person, period, parameters):
    """Whether the person pays no income tax above the basic rates.

    Apply the rates that s. 55B(2)(b) and s. 55C(1)(c) permit for the year
    being calculated. From 2016-17 these include the savings nil rate; from
    2018-19 the Scottish list includes rates below basic and the intermediate
    rate. Where s. 55B(2)(ba) and s. 55C(1)(ca) apply, test dividends as if
    s. 13A were omitted.

    Gift Aid extends the rate limits by the grossed-up gift (s. 414(2)(b));
    it does not reduce taxable income. Before 2017-18 this test uses the
    basic rate limit for Scottish taxpayers, even though the model's
    historical Scottish liability currently reads the 2017-18 schedule. The
    test also follows the statute where the model's liability departs from
    it: it starts the dividend upper rate at the basic rate limit (ss. 10
    and 13), counts no savings nil rate before 2016-17 (FA 2016 s. 4(17)),
    and places the nil-rate slice above the starting rate limit for savings
    (s. 12A).

    The test reads income before the Marriage Allowance. Step 4 of s. 23
    charges tax at each rate before Step 6 deducts the tax reductions, and
    s. 55B(1) gives the allowance as a tax reduction. The model still takes
    the allowance off earned_taxable_income (#1947), so
    non_savings_taxable_income and the savings rate bands built on it would
    read this test back.
    """
    rates = parameters(period).gov.hmrc.income_tax.rates
    gross_gift = person("gift_aid_grossed_up", period)
    # Earnings, pensions, property and other non-savings income after
    # allowances, which go to it first: the income below savings and
    # dividends (s. 16). This reads non-savings taxable income before the
    # Marriage Allowance.
    non_savings = person("non_savings_income_after_allowances", period)
    # The Scottish higher rate follows the starter, basic and intermediate
    # rates; in 2017-18 the Scottish scale had only the basic rate below it.
    # Before 2017-18 the test holds a Scottish taxpayer to the basic rate
    # limit. Section 11A takes effect in 2016-17 (FA 2014 Sch. 38 para. 12,
    # SI 2015/2000 art. 3), when s. 11A(1) charged the Scottish basic rate on
    # income that would otherwise bear the basic rate. The model reads its
    # Scottish scale's 2017-18 values in earlier years too, so the test sets
    # the limit by the year.
    scottish = rates.scotland.rates
    basic_rate_limit = rates.uk.thresholds[1] + gross_gift
    if period.start.year < 2017 or len(scottish.rates) < 3:
        scottish_limit = basic_rate_limit
    elif len(scottish.rates) == 3:
        scottish_limit = scottish.thresholds[1] + gross_gift
    else:
        scottish_limit = scottish.thresholds[3] + gross_gift
    non_savings_limit = where(
        person("pays_scottish_income_tax", period),
        scottish_limit,
        basic_rate_limit,
    )
    # Savings sit above non-savings income (s. 16) and take the rest-of-UK
    # limits (s. 11D(6)). Up to the basic rate limit they bear a basic rate
    # or the starting rate for savings, both permitted: s. 12(1) charges the
    # starting rate only on savings that would otherwise bear a basic rate
    # (s. 12(1)(b) from 2017-18). Above the limit s. 55B(2)(b) permits only
    # the savings nil rate. Section 12A(1) to (4) charges it on the lowest
    # savings above the starting rate limit for savings, up to the savings
    # allowance; dividends sit above savings (s. 16) and leave this slice
    # where it is. The person fails the test if any savings above the basic
    # rate limit lie outside the slice.
    savings = max_(
        0,
        person("taxable_savings_interest_income", period)
        - person("received_allowances_savings_income", period),
    )
    # FA 2016 s. 4(17) gives the savings nil rate effect from 2016-17.
    if period.start.year < 2016:
        savings_allowance = 0
    else:
        savings_allowance = person("savings_allowance", period)
    below_dividends = non_savings + savings
    nil_rate_start = max_(non_savings, rates.savings_starter_rate.allowance)
    nil_rate_top = min_(below_dividends, nil_rate_start + savings_allowance)
    savings_above_basic = max_(0, below_dividends - max_(non_savings, basic_rate_limit))
    nil_rate_above_basic = max_(
        0, nil_rate_top - max_(nil_rate_start, basic_rate_limit)
    )
    savings_at_forbidden_rates = savings_above_basic - nil_rate_above_basic > 0
    # Dividends are the top slice, above all non-savings income and savings
    # (s. 16), counted before the dividend allowance. Section 13(2) charges
    # the dividend upper rate on dividends that would otherwise bear the
    # higher rate, which starts at the basic rate limit (s. 10(3)), extended
    # by the gross gift.
    dividends = max_(
        0,
        person("taxable_dividend_income", period)
        - person("received_allowances_dividend_income", period),
    )
    dividend_upper_limit = basic_rate_limit
    dividends_above_basic = (dividends > 0) & (
        below_dividends + dividends > dividend_upper_limit
    )
    return (
        (non_savings <= non_savings_limit)
        & ~savings_at_forbidden_rates
        & ~dividends_above_basic
    )


class meets_marriage_allowance_income_conditions(Variable):
    label = "Meets Marriage Allowance income conditions"
    documentation = (
        "Whether this person pays income tax only at rates that ITA 2007 "
        "s. 55B(2)(b) and (ba) allow for receiving the Marriage Allowance."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = [
        dict(
            title="Income Tax Act 2007 s. 55B(2)(b) and (ba)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
    ]

    def formula(person, period, parameters):
        return liable_only_at_marriage_allowance_rates(person, period, parameters)
