from policyengine_uk.model_api import *
from policyengine_uk.utils.pension_credit import employed_earnings_sources
from policyengine_uk.variables.gov.dwp.pension_credit.pension_credit_earnings_income_tax import (
    income_tax_with_inputs_zeroed,
)

# Taxed income that council_tax_reduction_applicable_income leaves out on the
# pensioner schemes' general route: the Scottish Carer Supplement (SSI
# 2012/319 reg 27(1)(j)(xxib)), miscellaneous income, benefits in kind (no
# scheme counts a payment in kind as earnings), and income from capital:
# savings interest, other investment income, dividends and the profits of a
# property business (property_income), such as rent from a property the
# applicant doesn't live in.
#
# In each pensioner scheme, a council disregards any actual income from
# capital, except income from the capital that Part 2 of the capital
# Schedule lists: life interests and liferents, rights to rent where the
# applicant has no reversionary interest, annuities, and property held under
# a trust that pays or may pay the applicant or partner. It disregards that
# income too while such capital totals £10,000 or less. A council counts
# other capital through tariff income and leaves Part 2 capital out of it
# (SSI 2012/319 reg 27(1)(i) and (2), reg 31(10), Sch 3 paras 21 and 22 and
# Sch 4 Part 2; SI 2012/2885 Sch 1 paras 16(1)(i), 17(11) and 37, Sch 5
# paras 22 and 23 and Sch 6 Part 2; WSI 2013/3029 Sch 1 paras 10(1)(i),
# 11(11) and 31, Sch 4 paras 22 and 23 and Sch 5 Part 2). So a council
# disregards the interest on savings in an ordinary bank deposit and the
# dividends on shares held outright, and counts the deposit and the shares
# through tariff income. The model has no input that marks capital as Part 2
# capital, and other_investment_income takes in interest from trusts and
# settlements, so council_tax_reduction_applicable_income counts none of
# this income on the pensioner route, and the formula deducts no tax on any
# of it. The model makes that general approximation of the income rules:
# where Part 2 capital above £10,000 yields such income, a council counts it
# and the model doesn't.
#
# The model taxes property profits through property_income alone. Without
# them, the finance-cost reduction comes to nil on the branch, because
# property_finance_costs_relieved caps the costs it relieves at the property
# profits, so the reduction goes with the rent. property_rental_income only
# measures receipts for the property allowance, which can't take taxable
# property income below the nil the branch leaves, so the formula keeps it.
# Rent for letting part of the home (sublet_income) counts on the pensioner
# route (council_tax_reduction_home_letting_income), so the formula keeps it
# too, with the income tax the model charges on it above the rent-a-room limit.
PENSIONER_UNCOUNTED_INCOME = [
    "scottish_carer_supplement",
    "miscellaneous_income",
    "benefits_in_kind",
    "savings_interest_income",
    "other_investment_income",
    "dividend_income",
    "property_income",
]

# The Step 7 charges of ITA 2007 s. 23 that income_tax_charges holds,
# other than the winter fuel payment charge
# (gov.hmrc.income_tax.step_7_additional_tax: the High Income Child
# Benefit Charge and the pension annual allowance charge). Neither falls
# on income the pensioner schemes count: through the first, HMRC
# recovers Child Benefit, which council_tax_reduction_applicable_income
# leaves out on the pensioner route, and the second falls on pension
# contributions.
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
        "savings interest, other investment income, dividends and the profits "
        "of a property business (property_income), with the finance-cost "
        "reduction that goes with them. In each pensioner scheme, a council "
        "disregards any actual income from capital, except income from the "
        "capital that Part 2 of the capital Schedule lists: life interests "
        "and liferents, rights to rent where the applicant has no "
        "reversionary interest, annuities, and property held under a trust "
        "that pays or may pay the applicant or partner. It disregards that "
        "income too while such capital totals £10,000 or less. A council "
        "counts other capital, such as "
        "savings in an ordinary bank deposit or shares held outright, through "
        "tariff income, and leaves Part 2 capital out of it. The model has no "
        "input that marks capital as Part 2 capital, and "
        "other_investment_income takes in interest from trusts and "
        "settlements, so council_tax_reduction_applicable_income counts none "
        "of the interest, other investment income, dividends or rent from "
        "property on the pensioner route, and the formula deducts no tax on "
        "any of it. The model makes that general approximation of the income "
        "rules: where Part 2 capital above £10,000 yields such income, a "
        "council counts it and the model doesn't. It also "
        "leaves out the Step 7 charges of ITA 2007 s. 23 that "
        "income_tax_charges holds, the High Income Child Benefit Charge and "
        "the pension annual allowance charge: through the first, HMRC "
        "recovers Child Benefit, which the pensioner schemes do not count, "
        "and the second falls on pension contributions, so the formula "
        "treats neither as tax payable on income taken into account. This is "
        "the tax on the rest of the income the pensioner schemes count, with "
        "the uncounted income above it. The "
        "formula zeroes those inputs and the charges on a branch that it "
        "drops afterwards, and builds the branch only when someone has "
        "uncounted income or a charge."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/27",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/31",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/3/paragraph/21",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/3/paragraph/22",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/4/part/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/16",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/37",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5/paragraph/22",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/5/paragraph/23",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/6/part/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/10",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/11",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/31",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/4/paragraph/22",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/4/paragraph/23",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/5/part/2",
    ]

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
