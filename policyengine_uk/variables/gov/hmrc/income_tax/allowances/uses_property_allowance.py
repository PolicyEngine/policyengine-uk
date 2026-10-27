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
# Income tax is tax before the winter fuel payment charge plus the charge.
# The tax before it, and the most the charge could be, need nobody's
# benefits; the charge itself needs everyone's.
BEFORE_CHARGE = [
    "income_tax_before_winter_fuel_payment_charge",
    "winter_fuel_payment_charge_ceiling",
]


def with_route(simulation, name, period, uses_allowance, variables):
    """Each person's values of the variables with the given choices of
    property allowance.

    A route can change the person's total income, which is after the
    property allowance, and their Pension Credit, and so whether the winter
    fuel payment charge applies (s.681I(1)(b) and (4)). The branch shares the
    simulation's cached arrays until it writes, and is dropped afterwards so
    a later period starts from a fresh branch.
    """
    while name in simulation.branches or name == simulation.branch_name:
        name += "_"
    branch = simulation.get_branch(name)
    try:
        branch.set_input("uses_property_allowance", period, uses_allowance)
        person = branch.populations["person"]
        return [person(variable, period) for variable in variables]
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
        "only if they elect for it; with finance costs to relieve, each "
        "election is made only if it lowers the person's own income tax, "
        "including the winter fuel payment charge, with everyone else's "
        "route held fixed. Tax before the charge settles that comparison "
        "wherever the most the charge could be on either route "
        "(winter_fuel_payment_charge_ceiling) cannot reverse it; the charge "
        "itself, which needs everyone's benefits on each route, is worked "
        "out only where it can. "
        "Ties keep the default, so a person with receipts within the "
        "allowance keeps full relief even where electing out would carry "
        "finance costs forward. Without finance costs to relieve, the "
        "allowance is used whenever it lowers taxable property income, "
        "without comparing tax. That is always the lower tax before the "
        "winter fuel payment charge. While the charge has effect it can "
        "rarely cost more: the lower tax can raise the income Pension Credit "
        "counts and end an award that exempts the person from the charge. "
        "The model does not compare routes for these landlords, because "
        "that works out the benefits on both routes for the whole "
        "population and made simulations several times slower; on the "
        "Enhanced FRS the comparison changed no one's tax."
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
        # lower tax before the winter fuel payment charge, so the allowance
        # is used without comparing. The charge can rarely reverse that
        # (lower tax can end Pension Credit and with it the exemption,
        # s.681I(4)); see the documentation for why that is not compared.
        uses = lowers_income & ~reduction_at_stake
        choosing = lowers_income & reduction_at_stake
        if not choosing.any():
            # Nobody has a choice to weigh: skip the branches.
            return uses
        # Full relief applies unless electing out of it (s. 783BJ) lowers
        # tax; partial relief applies only if electing for it (s. 783BK)
        # lowers tax. Until a person decides, they keep that default.
        full_relief = person("property_receipts_within_allowance", period)
        route = where(choosing, full_relief, uses)
        for variable in INDEPENDENT_OF_ROUTE:
            person(variable, period)
        simulation = person.simulation
        # One person per household decides at a time, with everyone else's
        # route held fixed: another member's route can move this person's
        # tax (a partner's through the Marriage Allowance; anyone's, through
        # the shared winter fuel payment, when it changes who is entitled),
        # and comparing their switches at once would count that. Rounds
        # repeat until nobody in the household changes, for at most
        # MAX_ROUNDS: routes still changing in the last round are kept as
        # they stand. With one person deciding in a household, everyone
        # else's route is fixed throughout, so one round settles it.
        # Households do not move each other's tax, so each keeps its own
        # place in that order, and every household's next decision is
        # compared in the same pair of branches.
        order = person.get_rank(
            person.household, np.zeros(person.count), condition=choosing
        )
        deciders = person.household.sum(choosing)
        rank = np.zeros(person.count, dtype=int)
        rounds = np.ones(person.count, dtype=int)
        changed = np.zeros(person.count, dtype=bool)
        done = deciders == 0
        while not done.all():
            deciding = choosing & ~done & (order == rank)
            using = route | deciding
            not_using = route & ~deciding
            tax_using, most_charge_using = with_route(
                simulation, "property_allowance_used", period, using, BEFORE_CHARGE
            )
            tax_not_using, most_charge_not_using = with_route(
                simulation,
                "property_allowance_not_used",
                period,
                not_using,
                BEFORE_CHARGE,
            )
            # On each route the charge is between nothing and its ceiling,
            # so the allowance saves at least the saving before the charge
            # less the ceiling using it, and at most that saving plus the
            # ceiling not using it. Where those bounds share a sign, beyond a
            # penny and float32 rounding, the choice is the one tax
            # including the charge gives.
            saving = tax_not_using - tax_using
            rounding = 0.01 + 1e-6 * (abs(tax_using) + abs(tax_not_using))
            unsettled = (
                deciding
                & ((most_charge_using > 0) | (most_charge_not_using > 0))
                & (saving - most_charge_using < rounding)
                & (saving + most_charge_not_using > -rounding)
            )
            if (deciding & ~unsettled).any():
                # The rest wait, and their households with them, until no
                # household can decide without the charge.
                deciding = deciding & ~unsettled
            else:
                # Every household's next decision turns on the charge:
                # compare them all on income tax including it, worked out on
                # each route where some ceiling is above nothing (where it is
                # nothing, so is the charge, and tax before it is the tax).
                if (unsettled & (most_charge_using > 0)).any():
                    (tax_using,) = with_route(
                        simulation,
                        "property_allowance_used",
                        period,
                        using,
                        ["income_tax"],
                    )
                if (unsettled & (most_charge_not_using > 0)).any():
                    (tax_not_using,) = with_route(
                        simulation,
                        "property_allowance_not_used",
                        period,
                        not_using,
                        ["income_tax"],
                    )
            # Tax is computed to the penny; smaller differences are rounding.
            saving = np.round(tax_not_using - tax_using, 2)
            prefers_allowance = where(full_relief, saving >= 0, saving > 0)
            decided = where(deciding, prefers_allowance, route)
            changed = changed | person.household.any(decided != route)
            route = decided
            # Each household that decided moves to its next decider, and at
            # the end of a round to another round or to its settled routes.
            moved = person.household.any(deciding)
            rank = where(moved, rank + 1, rank)
            round_over = moved & (rank == deciders)
            again = round_over & changed & (deciders > 1) & (rounds < MAX_ROUNDS)
            done = done | (round_over & ~again)
            rank = where(again, 0, rank)
            rounds = where(again, rounds + 1, rounds)
            changed = changed & ~round_over
        return route
