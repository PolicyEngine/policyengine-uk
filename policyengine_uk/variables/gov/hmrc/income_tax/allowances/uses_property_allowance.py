from policyengine_uk.model_api import *

# Inputs to income tax that do not depend on how property profits are
# computed. Resolving them before branching lets both branches reuse them.
INDEPENDENT_OF_ROUTE = [
    "taxable_employment_income",
    "taxable_self_employment_income",
    "taxable_pension_income",
    "taxable_social_security_income",
    "taxable_savings_interest_income",
    "taxable_dividend_income",
    "taxable_miscellaneous_income",
    "pays_scottish_income_tax",
    "other_tax_credits",
]


def income_tax_with_route(simulation, name, period, uses_allowance):
    """Each person's income tax with the given choices of property allowance.

    The branch shares the simulation's cached arrays until it writes, and is
    dropped afterwards so a later period starts from a fresh branch.
    """
    while name in simulation.branches or name == simulation.branch_name:
        name += "_"
    branch = simulation.get_branch(name)
    try:
        branch.set_input("uses_property_allowance", period, uses_allowance)
        return branch.populations["person"]("income_tax", period)
    finally:
        del simulation.branches[name]


class uses_property_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Uses the property allowance"
    documentation = (
        "Whether the person's property profits are computed with the property "
        "allowance, by full relief or an election for partial relief, rather "
        "than with actual expenses and the finance-cost tax reduction. The "
        "two cannot be combined. Full relief applies to receipts within the "
        "allowance unless the person elects out of it, and partial relief "
        "only if they elect for it; each election is made only if it lowers "
        "the person's income tax. Without finance costs to relieve, the "
        "allowance is used whenever it lowers taxable property income."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BE",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BE",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BJ",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BJ",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BK",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BK",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005, s. 783BL",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783BL",
        ),
    ]

    def formula(person, period, parameters):
        deduction = person("property_allowance_deduction_if_used", period)
        profit = person("property_income", period) - person(
            "deductible_property_finance_costs", period
        )
        lowers_income = deduction > 0
        # The finance-cost reduction needs property profits to relieve.
        reduction_at_stake = (
            person("property_finance_costs_relievable", period) > 0
        ) & (profit > 0)
        # Without a reduction at stake, the allowance is used whenever it
        # lowers taxable property income. Otherwise compare income tax on
        # each route.
        uses = lowers_income & ~reduction_at_stake
        choosing = lowers_income & reduction_at_stake
        if not choosing.any():
            # Nobody has a choice to weigh: skip the branches.
            return uses
        for variable in INDEPENDENT_OF_ROUTE:
            person(variable, period)
        simulation = person.simulation
        tax_using = income_tax_with_route(
            simulation, "property_allowance_used", period, uses | choosing
        )
        tax_not_using = income_tax_with_route(
            simulation, "property_allowance_not_used", period, uses
        )
        # Tax is computed to the penny; smaller differences are rounding.
        saving = np.round(tax_not_using - tax_using, 2)
        # The allowance removes all of the profit exactly when receipts are
        # within it. Full relief then applies unless electing out of it
        # (s. 783BJ) lowers tax; partial relief applies only if electing for
        # it (s. 783BK) lowers tax.
        full_relief = deduction >= profit
        prefers_allowance = where(full_relief, saving >= 0, saving > 0)
        return where(choosing, prefers_allowance, uses)
