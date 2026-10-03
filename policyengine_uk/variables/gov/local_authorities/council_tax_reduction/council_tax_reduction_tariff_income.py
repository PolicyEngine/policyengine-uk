from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
    is_wales_scheme,
)
from policyengine_uk.variables.household.demographic.country import Country


def tariff_amount(capital, tariff, capital_limit):
    # `amount` for each complete `step` of capital above `threshold`, and
    # `amount` for any part of a step. Capital above the limit leaves no
    # entitlement, so it is not counted.
    excess = max_(0, min_(capital, capital_limit) - tariff.threshold)
    return np.ceil(excess / tariff.step) * tariff.amount


class council_tax_reduction_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction tariff income from capital"
    documentation = (
        "Income the national Council Tax Reduction schemes (England for "
        "pensioners, Wales and Scotland) treat capital as yielding, annualised. "
        "Pensioners: £1 a week for each £500, or part of £500, of capital over "
        "£10,000. People under pension age in Wales and Scotland: £1 a week "
        "for each £250, or part of £250, over £6,000; with an award of "
        "Universal Credit, the Universal Credit assumed yield of £4.35 a month "
        "for each £250, or part, over £6,000, which the Welsh scheme and the "
        "Scottish scheme to March 2022 take from the Secretary of State's "
        "assessment of income and the Scottish scheme from April 2022 sets at "
        "the same rate. Nil for the Pension Credit routes, whose income "
        "already includes the Pension Credit deemed income (or is wholly "
        "disregarded), for people on Income Support, income-based "
        "Jobseeker's Allowance or income-related Employment and Support "
        "Allowance, whose whole capital the Welsh scheme and the Scottish "
        "scheme to March 2022 disregard and whose income the Scottish scheme "
        "from April 2022 does not assess, and for English people under "
        "pension age, whose local schemes set their own tariff income."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/37",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/31",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/33",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/10/paragraph/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/27",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/26",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/51",
        "https://www.legislation.gov.uk/ssi/2012/303/schedule/5/paragraph/7",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/13",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/63",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/72",
    ]

    def formula(benunit, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        england_p = local_authorities.england.council_tax_reduction.pensioners
        wales_p = local_authorities.wales.council_tax_reduction.means_test
        scotland_p = local_authorities.scotland.council_tax_reduction.means_test
        uc_tariff = parameters(
            period
        ).gov.dwp.universal_credit.means_test.capital.tariff_income
        country = benunit.household("country", period)
        england = country == Country.ENGLAND
        wales = is_wales_scheme(country)
        scotland = is_scotland_scheme(country)
        capital = benunit("council_tax_reduction_assessable_capital", period)
        pensioner_weekly = select(
            [england, wales, scotland],
            [
                tariff_amount(
                    capital,
                    england_p.means_test.tariff_income,
                    england_p.means_test.capital_limit,
                ),
                tariff_amount(
                    capital,
                    wales_p.tariff_income.pensioner,
                    wales_p.capital_limit,
                ),
                tariff_amount(
                    capital,
                    scotland_p.tariff_income.pensioner,
                    scotland_p.capital_limit,
                ),
            ],
            default=0,
        )
        working_age_weekly = select(
            [wales, scotland],
            [
                tariff_amount(
                    capital,
                    wales_p.tariff_income.working_age,
                    wales_p.capital_limit,
                ),
                tariff_amount(
                    capital,
                    scotland_p.tariff_income.working_age,
                    scotland_p.capital_limit,
                ),
            ],
            default=0,
        )
        universal_credit_monthly = select(
            [wales, scotland],
            [
                tariff_amount(capital, uc_tariff, wales_p.capital_limit),
                tariff_amount(capital, uc_tariff, scotland_p.capital_limit),
            ],
            default=0,
        )
        pensioner = benunit("council_tax_reduction_pensioner", period)
        has_uc_award = benunit("universal_credit", period) > 0
        income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        tariff_income = select(
            [pensioner, has_uc_award, income_based_benefit],
            [
                pensioner_weekly * WEEKS_IN_YEAR,
                universal_credit_monthly * MONTHS_IN_YEAR,
                0,
            ],
            default=working_age_weekly * WEEKS_IN_YEAR,
        )
        pension_credit_route = benunit(
            "in_receipt_of_guarantee_credit", period
        ) | benunit("in_receipt_of_savings_credit_only", period)
        return where(pension_credit_route, 0, tariff_income)
