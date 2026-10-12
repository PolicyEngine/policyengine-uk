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
    """
    rates = parameters(period).gov.hmrc.income_tax.rates
    savings = person("taxable_savings_interest_income", period)
    dividends = person("taxable_dividend_income", period)
    # Earnings, pensions, property and other non-savings income after
    # allowances, as in property_income_tax.
    non_savings = max_(
        0,
        person("adjusted_net_income", period)
        - savings
        - dividends
        - person("allowances", period),
    )
    # The Scottish higher rate follows the starter, basic and intermediate
    # rates; before 2018-19 the Scottish scale had only the basic rate below it.
    scottish = rates.scotland.rates
    scottish_higher = scottish.thresholds[3 if len(scottish.rates) > 3 else 1]
    non_savings_limit = where(
        person("pays_scottish_income_tax", period),
        scottish_higher,
        rates.uk.thresholds[1],
    )
    savings_above_basic = add(
        person, period, ["higher_rate_savings_income", "add_rate_savings_income"]
    )
    # Dividends are the top slice, above all non-savings income (property
    # included) and savings (s. 16), counted before the dividend allowance;
    # the dividend upper rate starts at the basic rate limit (s. 13). The
    # savings test above uses the model's own savings bands.
    below_dividends = non_savings + max_(
        0, savings - person("received_allowances_savings_income", period)
    )
    dividends_after_allowances = max_(
        0, dividends - person("received_allowances_dividend_income", period)
    )
    dividends_above_basic = (dividends_after_allowances > 0) & (
        below_dividends + dividends_after_allowances > rates.uk.thresholds[1]
    )
    return (
        (non_savings <= non_savings_limit)
        & (savings_above_basic <= 0)
        & ~dividends_above_basic
    )


class meets_marriage_allowance_income_conditions(Variable):
    label = "Meets Marriage Allowance income conditions"
    documentation = (
        "Whether this person pays income tax only at the rates that allow a "
        "Marriage Allowance election, given their actual allowances. The "
        "gaining party must meet this (ITA 2007 s. 55B(2)(b), (ba)); the "
        "electing spouse must meet it with their allowance already cut by "
        "the transferable amount (s. 55C(1)(c), (ca))."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = [
        dict(
            title="Income Tax Act 2007 s. 55B(2)(b) and (ba)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
        dict(
            title="Income Tax Act 2007 s. 55C(1)(c) and (ca)",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55C",
        ),
    ]

    def formula(person, period, parameters):
        return liable_only_at_marriage_allowance_rates(person, period, parameters)
