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

    The test reads income before the Marriage Allowance. The rates a person
    is liable at come from Step 3 of s. 23, before the tax reductions of
    Step 6, of which the allowance is one (s. 55B(1)). The model still takes
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
    # Before 2017-18 the Scottish rates used the UK limits.
    scottish = rates.scotland.rates
    basic_rate_limit = rates.uk.thresholds[1] + gross_gift
    if len(scottish.rates) > 3:
        scottish_limit = scottish.thresholds[3] + gross_gift
    elif len(scottish.rates) == 3:
        scottish_limit = scottish.thresholds[1] + gross_gift
    else:
        scottish_limit = basic_rate_limit
    non_savings_limit = where(
        person("pays_scottish_income_tax", period),
        scottish_limit,
        basic_rate_limit,
    )
    # Savings sit above non-savings income (s. 16) and take the rest-of-UK
    # bands (s. 11D(6)). The starting rate for savings and then the savings
    # nil rate take the first of them, as in higher_rate_savings_income; the
    # model keeps the starting rate within the basic rate band. Savings above
    # those are charged at a positive rate, and fail the test once they pass
    # the basic rate limit.
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
    nil_rate_savings = starting_rate_savings + person("savings_allowance", period)
    savings_above_basic = (savings > nil_rate_savings) & (
        non_savings + savings > basic_rate_limit
    )
    # Dividends are the top slice, above all non-savings income and savings
    # (s. 16), counted before the dividend allowance. The dividend upper rate
    # starts at the basic rate limit (s. 13(2)), extended by the gross gift;
    # dividend_income_tax reads that limit from the dividend scale.
    dividends = max_(
        0,
        person("taxable_dividend_income", period)
        - person("received_allowances_dividend_income", period),
    )
    dividend_upper_limit = rates.dividends.thresholds[1] + gross_gift
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
        "Whether this person pays income tax only at the rates that let them "
        "receive the Marriage Allowance (ITA 2007 s. 55B(2)(b) and (ba))."
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
