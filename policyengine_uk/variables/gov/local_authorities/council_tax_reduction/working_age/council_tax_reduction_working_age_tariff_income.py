from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
    is_wales_scheme,
)


class council_tax_reduction_working_age_tariff_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction tariff income"
    documentation = (
        "Annual tariff income from capital in a working-age council tax "
        "reduction claim in Scotland or Wales: £1 a week for each £250, or "
        "part of £250, above £6,000. A Welsh applicant with Universal Credit "
        "has none, because the Universal Credit income figure already "
        "includes Universal Credit's own assumed yield from capital."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/63",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/33",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.local_authorities
        country = benunit.household("country", period)
        scotland = is_scotland_scheme(country)
        wales = is_wales_scheme(country)
        scot = p.scotland.council_tax_reduction.working_age.tariff_income
        welsh = p.wales.council_tax_reduction.working_age.tariff_income
        threshold = where(scotland, scot.threshold, welsh.threshold)
        step = where(scotland, scot.step, welsh.step)
        amount = where(scotland, scot.amount, welsh.amount)
        capital = benunit("council_tax_reduction_working_age_capital", period)
        steps = np.ceil(max_(0, capital - threshold) / step)
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        applies = ~(wales & has_universal_credit)
        return applies * steps * amount * WEEKS_IN_YEAR
