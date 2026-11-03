from policyengine_uk.model_api import *
from policyengine_uk.utils.pension_credit import employed_earnings_sources
from policyengine_uk.variables.gov.dwp.pension_credit.pension_credit_earnings_income_tax import (
    income_tax_with_inputs_zeroed,
)

# Taxed income that council_tax_reduction_applicable_income leaves out on the
# pensioner schemes' general route: the Scottish Carer Supplement (SSI
# 2012/319 reg 27(1)(j)(xxib)), miscellaneous income, benefits in kind (no
# scheme counts a payment in kind as earnings), savings interest and other
# investment income, and dividends.
PENSIONER_UNCOUNTED_INCOME = [
    "scottish_carer_supplement",
    "miscellaneous_income",
    "benefits_in_kind",
    "savings_interest_income",
    "other_investment_income",
    "dividend_income",
]

# The Step 7 charges of ITA 2007 s. 23 other than the winter fuel payment
# charge (gov.hmrc.income_tax.step_7_additional_tax: the High Income Child
# Benefit Charge and the pension annual allowance charge). Neither falls on
# income the pensioner schemes count: the first recovers Child Benefit, which
# council_tax_reduction_applicable_income leaves out on the pensioner route,
# and the second falls on pension contributions.
STEP_7_CHARGES = ["income_tax_charges"]


class council_tax_reduction_income_tax_on_other_counted_income(Variable):
    value_type = float
    entity = Person
    label = "Income tax on the other income a pensioner Council Tax Reduction counts"
    documentation = (
        "The person's income tax before the winter fuel payment charge if "
        "nobody in the simulation had employed earnings (employment income "
        "and statutory sick, maternity and paternity pay), self-employment "
        "income, or the taxed income the pensioner schemes do not count: the "
        "Scottish Carer Supplement, miscellaneous income, benefits in kind, "
        "savings interest, other investment income and dividends. It also "
        "leaves out the Step 7 charges of ITA 2007 s. 23 that "
        "income_tax_charges holds, the High Income Child Benefit Charge and "
        "the pension annual allowance charge: the first recovers Child "
        "Benefit, which the pensioner schemes do not count, and the second "
        "falls on pension contributions, so neither is tax payable on income "
        "taken into account. This is the tax on the rest of the income the "
        "pensioner schemes count, with the uncounted income above it. The "
        "formula zeroes those inputs and the charges on a branch that it "
        "drops afterwards, and builds the branch only when someone has "
        "uncounted income or a charge."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        zeroed = PENSIONER_UNCOUNTED_INCOME + STEP_7_CHARGES
        if not any((person(variable, period) != 0).any() for variable in zeroed):
            return person("pension_credit_income_tax_without_earnings", period)
        return income_tax_with_inputs_zeroed(
            person.simulation,
            period,
            employed_earnings_sources(parameters, period)
            + ["self_employment_income"]
            + zeroed,
        )
