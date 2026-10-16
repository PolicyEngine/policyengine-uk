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
# Rounds of decisions within a household before the routes are taken as
# settled. Members' routes interact only through small amounts (such as the
# Marriage Allowance, or a shared winter fuel payment and so its charge), so
# a second round rarely changes anything.
MAX_ROUNDS = 3


def income_tax_with_route(simulation, name, period, uses_allowance):
    """Each person's income tax with the given choices of property allowance.

    The tax includes the winter fuel payment charge. A route can change the
    person's total income, which is after the property allowance, and their
    Pension Credit, and so whether the charge applies (s.681I(1)(b) and (4)).
    The branch shares the simulation's cached arrays
    until it writes, and is dropped afterwards so a later period starts from
    a fresh branch.
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
        "the person's own income tax, including the winter fuel payment "
        "charge, with everyone else's route held fixed. "
        "Ties keep the default, so a person with receipts within the "
        "allowance keeps full relief even where electing out would carry "
        "finance costs forward. Without finance costs to relieve, the "
        "default is the allowance whenever it lowers taxable property "
        "income. Before the winter fuel payment charge that default is "
        "always the lower tax, so it is taken without comparing. While the "
        "charge has effect, lower tax before the charge can end an award "
        "that exempts the person from it, so the routes are compared."
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
        # Without a reduction at stake, lower taxable property income means
        # lower tax before the winter fuel payment charge. The charge can
        # reverse that: lower tax can raise income that Pension Credit
        # counts, end the award and with it the exemption (s.681I(4)), and
        # the charge can exceed the saving. So while it has effect, compare
        # income tax on each route for everyone the allowance would help.
        charge_in_effect = parameters(
            period
        ).gov.hmrc.income_tax.charges.winter_fuel_payment.in_effect
        compared = reduction_at_stake | charge_in_effect
        uses = lowers_income & ~compared
        choosing = lowers_income & compared
        if not choosing.any():
            # Nobody has a choice to weigh: skip the branches.
            return uses
        # With a reduction at stake, full relief applies unless electing out
        # of it (s. 783BJ) lowers tax, and partial relief applies only if
        # electing for it (s. 783BK) lowers tax. Without one, the allowance
        # is the default. Until a person decides, they keep their default.
        full_relief = person("property_receipts_within_allowance", period)
        default = full_relief | ~reduction_at_stake
        route = where(choosing, default, uses)
        for variable in INDEPENDENT_OF_ROUTE:
            person(variable, period)
        simulation = person.simulation
        # One person per household decides at a time, with everyone else's
        # route held fixed: another member's route can move this person's
        # tax (a partner's through the Marriage Allowance; anyone's, through
        # the shared winter fuel payment, when it changes who is entitled),
        # and comparing their switches at once would count that. Rounds
        # repeat until nobody changes.
        order = person.get_rank(
            person.household, np.zeros(person.count), condition=choosing
        )
        for _ in range(MAX_ROUNDS):
            changed = False
            for rank in range(int(order.max()) + 1):
                deciding = choosing & (order == rank)
                tax_using = income_tax_with_route(
                    simulation, "property_allowance_used", period, route | deciding
                )
                tax_not_using = income_tax_with_route(
                    simulation,
                    "property_allowance_not_used",
                    period,
                    route & ~deciding,
                )
                # Tax is computed to the penny; smaller differences are
                # rounding.
                saving = np.round(tax_not_using - tax_using, 2)
                prefers_allowance = where(default, saving >= 0, saving > 0)
                decided = where(deciding, prefers_allowance, route)
                changed = changed or bool((decided != route).any())
                route = decided
            # With one person deciding per household, everyone else's route
            # was fixed throughout, so one round settles it.
            if order.max() == 0 or not changed:
                break
        return route
