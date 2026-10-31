from policyengine_uk.model_api import *
from policyengine_uk.utils.company_car import share_of_year_available


class company_car_benefit(Variable):
    value_type = float
    entity = Person
    label = "Company car benefit"
    documentation = (
        "The cash equivalent of the benefit of the person's company car, "
        "treated as earnings from their employment (ITEPA 2003 s. 120), "
        "following the steps of s. 121(1): the price of the car and its "
        "accessories, less capital contributions up to the cap (s. 132), "
        "times the appropriate percentage, reduced in proportion to the "
        "days the car is unavailable (s. 143), less payments for private "
        "use, and nil if those payments are at least that amount (s. 144). "
        "Not modelled: optional remuneration arrangements (s. 120A), "
        "classic cars (s. 147), shared and pool cars (ss. 148 and 167), and "
        "vans (s. 154 onwards). Calculated from 2020-21."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "has_company_car"
    reference = [
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 120",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/120",
        ),
        dict(
            title="Income Tax (Earnings and Pensions) Act 2003 s. 121",
            href="https://www.legislation.gov.uk/ukpga/2003/1/section/121",
        ),
        dict(
            title="HMRC 480 Chapter 12: how to work out the benefit of a company car",
            href="https://www.gov.uk/guidance/how-to-work-out-the-benefit-of-a-company-car-480-chapter-12",
        ),
    ]

    def formula_2020(person, period, parameters):
        p = parameters(period).gov.hmrc.income_tax.benefits_in_kind.company_car
        # Steps 1 and 2: the price of the car and its accessories.
        price = max_(person("company_car_list_price", period), 0)
        # Step 3: capital contributions, up to the cap (s. 132(3)).
        contributions = min_(
            max_(person("company_car_capital_contributions", period), 0),
            p.capital_contribution_cap,
        )
        interim_sum = max_(price - contributions, 0)
        # Steps 5 and 6: the appropriate percentage of the interim sum.
        full_year = interim_sum * person("company_car_appropriate_percentage", period)
        # Step 7: s. 143(3) deducts A x U / Y for the days unavailable.
        provisional_sum = full_year * share_of_year_available(person, period)
        # Step 8: payments for private use (s. 144).
        payments = max_(person("company_car_private_use_payments", period), 0)
        return max_(provisional_sum - payments, 0)
