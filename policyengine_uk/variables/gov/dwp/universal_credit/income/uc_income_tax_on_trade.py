from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_income_tax import uc_income_tax_on_earnings_slice


class uc_income_tax_on_trade(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit deduction for income tax on the person's trade"
    documentation = (
        "The part of uc_income_tax_on_earnings paid in respect of the "
        "person's trade, profession or vocation, which reg. 57(2) step 3 "
        "deducts inside the self-employed earnings calculation: the tax on "
        "their earnings less the tax on their other earnings alone. The "
        "other earnings are taken as the lower slice, as PAYE codes give "
        "the personal allowance to an employment first; the rest of the "
        "tax on earnings is in respect of the employment (reg. 55(5)(b))."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2), step 3",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 55(5)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
    ]

    def formula(person, period, parameters):
        with_trade = uc_income_tax_on_earnings_slice(person, period, parameters)
        without_trade = uc_income_tax_on_earnings_slice(
            person, period, parameters, include_trade=False
        )
        # Never more than the tax on earnings in use, which can be an input:
        # the rest of that figure is in respect of the employment.
        return min_(
            with_trade - without_trade, person("uc_income_tax_on_earnings", period)
        )
