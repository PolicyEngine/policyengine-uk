from policyengine_uk.model_api import *
from policyengine_uk.utils.pension_credit import employed_earnings_sources
from policyengine_uk.variables.gov.dwp.pension_credit.pension_credit_earnings_income_tax import (
    DECISION,
    person_variable_with_inputs_zeroed,
)


class legacy_means_test_uncounted_income_tax_without_earnings(Variable):
    value_type = float
    entity = Person
    label = "Income tax on income the legacy means tests do not count, without earnings"
    documentation = (
        "The part of the person's income tax before the winter fuel payment "
        "charge, if nobody in the simulation had employed earnings (employment "
        "income and statutory sick, maternity and paternity pay) or "
        "self-employment income, that is not tax on income the legacy means "
        "tests take into account: the tax on rent from property, interest and "
        "dividends, and the other Step 7 charges. Rent from boarders, lodgers "
        "and sub-tenants in the home falls outside that list: the tests count "
        "it, so legacy_means_test_income_tax holds its tax "
        "(rent_a_room_income_tax). It is that pre-charge tax "
        "less legacy_means_test_income_tax, both on the branch without "
        "earnings, floored at nil. Income Support, Housing Benefit, Pension "
        "Credit and council tax reduction treat income derived from capital "
        "as capital and disregard tax only on income they take into account "
        "(IS Regs 1987 Sch 9 paras 1 and 22; HB Regs 2006 Sch 5 paras 1 and "
        "17; HB (SPC) Regs 2006 reg 33(12) and Sch 5 para 22; SPC Regs 2002 "
        "reg 17(10)(a) and Sch IV para 18), so none of them deducts this tax "
        "(legacy_means_test_deducted_income_tax). It is measured without "
        "earnings because the tax on earnings is the extra tax the earnings "
        "cause, including on savings, dividends and rent, and the tests do "
        "deduct that. " + DECISION
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/5",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/33",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IV",
    )

    def formula(person, period, parameters):
        income_tax = person("pension_credit_income_tax_without_earnings", period)
        # Zero the same earnings as pension_credit_income_tax_without_earnings,
        # so both taxes describe the same world without earnings.
        sources = employed_earnings_sources(parameters, period) + [
            "self_employment_income"
        ]
        if not any((person(source, period) != 0).any() for source in sources):
            counted = person("legacy_means_test_income_tax", period)
        else:
            counted = person_variable_with_inputs_zeroed(
                person.simulation,
                period,
                sources,
                "legacy_means_test_income_tax",
            )
        return max_(0, income_tax - counted)
