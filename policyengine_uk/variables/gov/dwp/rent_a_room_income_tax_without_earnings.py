from policyengine_uk.model_api import *
from policyengine_uk.utils.pension_credit import employed_earnings_sources
from policyengine_uk.variables.gov.dwp.pension_credit.pension_credit_earnings_income_tax import (
    DECISION,
    person_variable_with_inputs_zeroed,
)


class rent_a_room_income_tax_without_earnings(Variable):
    value_type = float
    entity = Person
    label = "Income tax on rent-a-room income, without earnings"
    documentation = (
        "rent_a_room_income_tax_after_reductions if nobody in the simulation "
        "had employed earnings (employment income and statutory sick, "
        "maternity and paternity pay) or self-employment income. Where a "
        "council tax reduction scheme does not count rent from boarders, "
        "lodgers and sub-tenants in the home (the Universal Credit route, and "
        "the Scottish working-age scheme while it does not list that income), "
        "council_tax_reduction_applicable_income treats the rent as uncounted "
        "income, as legacy_means_test_uncounted_income_tax_without_earnings "
        "treats income from capital: it leaves out of the deducted tax the "
        "tax this rent would bear without earnings, and keeps the extra tax "
        "that earnings cause on it. " + DECISION
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/37",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/57",
    )

    def formula(person, period, parameters):
        # The same world without earnings as
        # legacy_means_test_uncounted_income_tax_without_earnings.
        # Taxable rent-a-room income does not depend on earnings, so without
        # it there is no tax on it on any branch.
        if not (person("taxable_rent_a_room_income", period) > 0).any():
            return person.empty_array()
        sources = employed_earnings_sources(parameters, period) + [
            "self_employment_income"
        ]
        if not any((person(source, period) != 0).any() for source in sources):
            return person("rent_a_room_income_tax_after_reductions", period)
        return person_variable_with_inputs_zeroed(
            person.simulation,
            period,
            sources,
            "rent_a_room_income_tax_after_reductions",
        )
