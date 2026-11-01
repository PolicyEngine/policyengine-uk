from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_pensioner_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pensioner tariff income from capital"
    documentation = (
        "Weekly income that councils treat a pensioner's capital as "
        "yielding, annualised: £1 for each £500, or part of £500, of "
        "council_tax_reduction_assessable_capital above £10,000. The "
        "Secretary of State and the Welsh Ministers count the excess up to "
        "£16,000; the Scottish Ministers set no ceiling, though in every "
        "nation nobody with capital over £16,000 gets a reduction. We use "
        "the pension-age Housing Benefit tariff amounts, which all three "
        "nations share. We give nil on the Pension Credit routes: councils "
        "disregard the whole of a guarantee credit recipient's capital, and "
        "on a savings-credit-only award they use the Secretary of State's "
        "assessment of income, which already includes Pension Credit's "
        "deemed income from capital. We also give working-age families nil, "
        "because we do not model their tariff income here."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/37",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/14",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/31",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/27",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/24",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/25",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/29",
    )

    def formula(benunit, period, parameters):
        tariff = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.capital.pension_age.tariff_income
        local_authorities = parameters(period).gov.local_authorities
        country = benunit.household("country", period)
        capital = benunit("council_tax_reduction_assessable_capital", period)
        # SI 2012/2885 Sch 1 para 37 and WSI 2013/3029 Sch 1 para 31 count
        # the excess "not exceeding £16,000", the capital limit. The Scottish
        # Ministers set no ceiling in SSI 2012/319 reg 27(2); under reg 40
        # nobody with capital above £16,000 gets a reduction.
        counted_capital = select(
            [
                country == Country.ENGLAND,
                country == Country.WALES,
                country == Country.SCOTLAND,
            ],
            [
                min_(
                    capital,
                    local_authorities.england.council_tax_reduction.pensioners.means_test.capital_limit,
                ),
                min_(
                    capital,
                    local_authorities.wales.council_tax_reduction.means_test.capital_limit,
                ),
                capital,
            ],
            default=0,
        )
        excess_capital = max_(0, counted_capital - tariff.threshold)
        weekly_tariff_income = np.ceil(excess_capital / tariff.step) * tariff.amount
        # The Pension Credit routes (England Sch 1 paras 13 and 14, Wales
        # Sch 1 paras 7 and 8, Scotland regs 24 and 25), as in
        # council_tax_reduction_applicable_income. The benefit unit's
        # Pension Credit is its claimant's and partner's.
        applicant_family = ~benunit("council_tax_reduction_head_applies_alone", period)
        pension_credit_route = applicant_family & (
            benunit("in_receipt_of_guarantee_credit", period)
            | benunit("in_receipt_of_savings_credit_only", period)
        )
        pensioner = benunit("council_tax_reduction_pensioner", period)
        return where(
            pensioner & ~pension_credit_route,
            weekly_tariff_income * WEEKS_IN_YEAR,
            0,
        )
