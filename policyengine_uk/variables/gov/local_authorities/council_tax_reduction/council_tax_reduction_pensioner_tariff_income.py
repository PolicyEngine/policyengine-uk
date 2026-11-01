from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_pensioner_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pensioner tariff income from capital"
    documentation = (
        "Weekly income the pensioner Council Tax Reduction schemes treat "
        "capital as yielding, annualised: £1 for each £500, or part of £500, "
        "of council_tax_reduction_assessable_capital above £10,000, up to the "
        "£16,000 capital limit. England, Wales and Scotland use the "
        "pension-age Housing Benefit amounts. Nil where Pension Credit sets "
        "the means test: the guarantee credit disregards the whole of the "
        "capital, and on a savings-credit-only award the Secretary of "
        "State's assessment of income already includes Pension Credit's "
        "deemed income from capital. Nil for working-age families, whose "
        "tariff income is not modelled."
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
        capital_limit = select(
            [
                country == Country.ENGLAND,
                country == Country.WALES,
                country == Country.SCOTLAND,
            ],
            [
                local_authorities.england.council_tax_reduction.pensioners.means_test.capital_limit,
                local_authorities.wales.council_tax_reduction.means_test.capital_limit,
                local_authorities.scotland.council_tax_reduction.means_test.capital_limit,
            ],
            default=0,
        )
        capital = benunit("council_tax_reduction_assessable_capital", period)
        # SI 2012/2885 Sch 1 para 37 and WSI 2013/3029 Sch 1 para 31 count
        # the excess "not exceeding £16,000"; above it there is no reduction.
        excess_capital = max_(0, min_(capital, capital_limit) - tariff.threshold)
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
