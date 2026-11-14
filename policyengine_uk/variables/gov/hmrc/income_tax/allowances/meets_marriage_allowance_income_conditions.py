from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax_allocation import (
    share_meets_marriage_allowance_rate_test,
)


def liable_only_at_marriage_allowance_rates(person, period, parameters):
    """Whether the person pays no income tax above the basic rates.

    Apply the rates Parliament permits for the tax year (s. 55B(2)(b) and
    s. 55C(1)(c)). From 2016-17 these include the savings nil rate; from
    2018-19 the Scottish list includes rates below basic and the intermediate
    rate. Where s. 55B(2)(ba) and s. 55C(1)(ca) apply, test dividends as if
    s. 13A were omitted.

    Parliament extends the rate limits by the grossed-up Gift Aid gift
    (s. 414(2)(b)); the gift does not reduce taxable income. Before 2017-18
    this test uses the basic rate limit for Scottish taxpayers, even though
    the model's historical Scottish liability currently reads the 2017-18
    schedule. The test also follows the statute where the model's liability
    departs from it: it starts the dividend upper rate at the basic rate
    limit (ss. 10 and 13), counts no savings nil rate before 2016-17 (FA 2016
    s. 4(17)), and places the nil-rate slice above the starting rate limit
    for savings (s. 12A).

    Parliament charges tax at each rate at Step 4 and takes tax reductions
    off at Step 6 (s. 23), and it gives the allowance as a tax reduction at
    Step 6 (ss. 55A(2) and 55B(1)). So the allowance never changes the income
    each rate applies to, and this test never reads it:
    marriage_allowance_tax_reduction takes the allowance off the tax, and
    the test reads income after allowances and the savings, dividend and
    Gift Aid amounts directly.

    The test reads the share of reliefs and allowances the model holds
    (received_allowances_savings_income and
    received_allowances_dividend_income) and counts the share as meeting the
    test where it does either in float32, as the model always has, or in
    float64 from the amounts the model holds, as the search that sets the share
    (s. 25(2); policyengine_uk.utils.income_tax_allocation) counts it. So it
    gives the answer the search counted on. Income at a limit meets the test,
    since Parliament lets income reach each limit (s. 10(2)).
    """
    return share_meets_marriage_allowance_rate_test(person, period, parameters)


class meets_marriage_allowance_income_conditions(Variable):
    label = "Meets Marriage Allowance income conditions"
    documentation = (
        "Whether this person pays income tax only at rates that Parliament "
        "allows for receiving the Marriage Allowance (ITA 2007 s. 55B(2)(b) "
        "and (ba))."
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
