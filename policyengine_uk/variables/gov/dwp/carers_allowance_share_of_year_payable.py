from policyengine_uk.model_api import *


class carers_allowance_share_of_year_payable(Variable):
    value_type = float
    entity = Person
    label = "share of the year in which Carer's Allowance can be paid"
    documentation = (
        "The share of the year's weeks in which the earnings condition lets "
        "Carer's Allowance be paid. It is 1 for anyone at or below the "
        "earnings limit. Above it, the allowance stops in full except where "
        "the Budget 2026 earnings taper applies, so it is the share of the "
        "year the taper covers in England and Wales (182/365 in 2030-31 on "
        "the model's 6 October 2030 start, then 1) and 0 elsewhere. "
        "carers_allowance deducts overlapping benefits only for this share "
        "of the year, because the weekly overlap rule applies only in weeks "
        "the allowance is paid."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://assets.publishing.service.gov.uk/media/6ae1883fe4367e5c8b0467df/AB26_Policy_Costing.pdf#page=16",
    )

    def formula(person, period, parameters):
        taper = parameters(period).gov.dwp.carers_allowance.earnings_taper
        country = person.household("country", period).decode_to_str()
        tapers = np.isin(country, list(taper.countries)) * taper.applies
        gainfully_employed = person(
            "is_gainfully_employed_for_carers_allowance", period
        )
        return where(gainfully_employed, tapers, 1)
