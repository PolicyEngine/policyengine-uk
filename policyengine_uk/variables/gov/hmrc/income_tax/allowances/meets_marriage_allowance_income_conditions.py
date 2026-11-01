from policyengine_uk.model_api import *


def liable_only_at_marriage_allowance_rates(person, period, parameters):
    """Whether the person pays no income tax above the basic rates.

    ITA 2007 s. 55B(2)(b) and s. 55C(1)(c) allow only the basic rate, the
    property, default, savings, Scottish and Welsh basic rates, the Scottish
    starter and intermediate rates, the dividend ordinary rate and the nil and
    starting rates for savings. So no non-savings income may reach the higher
    rate (the Scottish higher rate for a Scottish taxpayer), and no savings the
    savings higher rate. Dividends covered by the dividend nil rate still
    count: s. 55B(2)(ba) and s. 55C(1)(ca) test the dividend upper rate as if
    s. 13A were omitted.

    The bands are the ones the model taxes with: Gift Aid extends the rate
    limits by the grossed-up gift (s. 414(2)(b)), as in earned_income_tax,
    and does not come off the income.

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
    # dividends (s. 16). It is non_savings_taxable_income before the
    # Marriage Allowance.
    non_savings = person("non_savings_income_after_allowances", period)
    # The Scottish higher rate follows the starter, basic and intermediate
    # rates; in 2017-18 the Scottish scale had only the basic rate below it.
    # Before 2017-18 a Scottish taxpayer's limit is the basic rate limit.
    # Section 11A takes effect in 2016-17 (FA 2014 Sch. 38 para. 12, SI
    # 2015/2000 art. 3), when s. 11A(1) charged the Scottish basic rate on
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
    # bands (s. 11D(6)). As in higher_rate_savings_income, the model charges
    # the first of them at the starting rate for savings, which it keeps
    # within the basic rate band, and then at the savings nil rate. Savings
    # above those bear a positive rate, and the person fails the test once
    # they pass the basic rate limit.
    savings = max_(
        0,
        person("taxable_savings_interest_income", period)
        - person("received_allowances_savings_income", period),
    )
    starter = rates.savings_starter_rate
    savings_in_basic_band = clip(
        non_savings + savings, rates.uk.thresholds[0], basic_rate_limit
    ) - clip(non_savings, rates.uk.thresholds[0], basic_rate_limit)
    starting_rate_savings = clip(
        min_(savings, savings_in_basic_band),
        0,
        max_(0, starter.allowance - non_savings * starter.phase_out),
    )
    # FA 2016 s. 4(17) gives the savings nil rate effect from 2016-17.
    if period.start.year < 2016:
        savings_allowance = 0
    else:
        savings_allowance = person("savings_allowance", period)
    nil_rate_savings = starting_rate_savings + savings_allowance
    savings_above_basic = (savings > nil_rate_savings) & (
        non_savings + savings > basic_rate_limit
    )
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
        non_savings + savings + dividends > dividend_upper_limit
    )
    return (
        (non_savings <= non_savings_limit)
        & ~savings_above_basic
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
