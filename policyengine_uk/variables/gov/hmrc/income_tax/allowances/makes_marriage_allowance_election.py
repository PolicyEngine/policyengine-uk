from policyengine_uk.model_api import *

BRANCH_OUTPUTS = [
    "income_tax",
    "personal_allowance",
    "marriage_allowance_tax_reduction_limit",
    "meets_marriage_allowance_income_conditions",
]
# Inputs to income tax that do not depend on the election. They are resolved
# before branching and held at the simulation's values in both branches, so
# the result does not depend on which variable a caller asks for first, and a
# choice made in branches upstream of them (a reform's split of adjusted net
# income, or a labour supply response in employment income) is not made again
# for the counterfactual.
INDEPENDENT_OF_ELECTION = [
    "age",
    "employment_income",
    "adjusted_net_income",
    "gift_aid_grossed_up",
    "gift_aid",
    "blind_persons_allowance",
    "covenanted_payments",
    "charitable_investment_gifts",
    "other_deductions",
    "pension_contributions_relief",
    "taxable_savings_interest_income",
    "taxable_dividend_income",
    "taxable_property_income",
    "pays_scottish_income_tax",
    "CB_HITC",
    "other_tax_credits",
    "married_couples_allowance",
]


def tax_position(simulation, name, period, relinquished, held):
    """Each person's tax with no election in force and the given allowance cut.

    The branch holds the election off, so no one gains a reduction, and cuts
    each person's personal allowance by ``relinquished`` (ITA 2007 s. 55B(6)).
    It also holds each variable in ``held`` at the given values, the
    simulation's own: the inputs to income tax the election does not change,
    and the property allowance route. From policyengine-core 3.33, an input
    set on a branch drops what the branch holds that may have been calculated
    from the value it replaces. A choice the simulation made in branches of
    its own before this election (the property allowance route, say) was
    weighed with an election in force there, so without these inputs the
    branch would make that choice again for the counterfactual it represents.
    The branch shares the simulation's cached arrays until it writes, and is
    dropped afterwards so a later period starts from a fresh branch.
    """
    while name in simulation.branches or name == simulation.branch_name:
        name += "_"
    branch = simulation.get_branch(name)
    try:
        branch.set_input(
            "makes_marriage_allowance_election",
            period,
            np.zeros(len(relinquished), dtype=bool),
        )
        branch.set_input("marriage_allowance_relinquished", period, relinquished)
        for variable, values in held.items():
            branch.set_input(variable, period, values)
        population = branch.populations["person"]
        return {variable: population(variable, period) for variable in BRANCH_OUTPUTS}
    finally:
        del simulation.branches[name]


class makes_marriage_allowance_election(Variable):
    value_type = bool
    entity = Person
    label = "Makes a Marriage Allowance election"
    documentation = (
        "Whether this person elects to give up part of their personal "
        "allowance so that their spouse or civil partner gets the Marriage "
        "Allowance tax reduction. The couple elects only when the election "
        "is allowed and lowers their combined income tax, in whichever "
        "direction lowers it more, and only if the spouse who would gain has "
        "would_claim_marriage_allowance true. Set as an input, an election "
        "is taken to be one the other spouse is entitled to gain from: the "
        "conditions are checked only when the model makes the choice."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 55B",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
        dict(
            title="Income Tax Act 2007 s. 55C",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55C",
        ),
        dict(
            title="Income Tax Act 2007 s. 55E",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55E",
        ),
    ]

    def formula(person, period, parameters):
        held = {
            variable: person(variable, period) for variable in INDEPENDENT_OF_ELECTION
        }
        spouse = person("is_marriage_allowance_spouse", period)
        transferable = person("marriage_allowance_transferable_amount", period)
        # The property allowance route (ITTOIA 2005 s. 783BL) is settled
        # first, each route weighed with the election it would bring. The
        # election is then weighed under that route.
        held["uses_property_allowance"] = person("uses_property_allowance", period)
        simulation = person.simulation
        without = tax_position(
            simulation,
            "marriage_allowance_without_election",
            period,
            np.zeros_like(transferable),
            held,
        )
        relinquishing = tax_position(
            simulation,
            "marriage_allowance_relinquishing",
            period,
            spouse * transferable,
            held,
        )

        def partner(values):
            # The other spouse's value, for each spouse.
            return person.benunit.sum(spouse * values) - spouse * values

        # If this person elects, the other spouse's tax falls by the
        # appropriate percentage of this person's transferable amount, capped
        # at the tax they have left (s. 55B(1), (3); s. 29(2)), and this
        # person pays tax on the allowance they give up.
        rate = person("marriage_allowance_appropriate_percentage", period)
        partner_reduction = min_(
            partner(rate) * transferable,
            partner(without["marriage_allowance_tax_reduction_limit"]),
        )
        extra_tax = relinquishing["income_tax"] - without["income_tax"]
        # Tax is computed to the penny; smaller differences are rounding.
        saving = np.round(partner_reduction - extra_tax, 2)
        married_couples_allowance_claimed = person.benunit.any(
            spouse & (person("married_couples_allowance", period) > 0)
        )
        allowed = (
            spouse
            # s. 55B(2)(d): neither spouse claims married couple's allowance.
            & ~married_couples_allowance_claimed
            # s. 55C(1)(b): the electing spouse is entitled to an allowance.
            & (without["personal_allowance"] > 0)
            # s. 55C(1)(c), (ca): only basic rates once the allowance is cut.
            & relinquishing["meets_marriage_allowance_income_conditions"]
            # s. 55B(2)(b), (ba): the gaining party pays only basic rates.
            & (partner(without["meets_marriage_allowance_income_conditions"]) > 0)
        )
        # Elect only to lower the couple's tax. Only one spouse elects. s. 55E
        # allows each of them one election and one reduction and does not
        # bar elections both ways, which would lower some couples' tax
        # further (where giving up allowance costs less than the basic rate,
        # as on dividends or at the Scottish starter rate), but HMRC's
        # guidance describes a single transfer from the lower earner.
        saving_if_allowed = where(allowed & (saving > 0), saving, 0)
        other_saving = partner(saving_if_allowed)
        # On a tie the spouse with the lower adjusted net income elects, then
        # the elder, then the first listed.
        income = person("adjusted_net_income", period)
        other_income = partner(income)
        elder = (
            person.get_rank(person.benunit, -person("age", period), condition=spouse)
            == 0
        )
        first_on_tie = (income < other_income) | ((income == other_income) & elder)
        chooses = (saving_if_allowed > 0) & (
            (saving_if_allowed > other_saving)
            | ((saving_if_allowed == other_saving) & first_on_tie)
        )
        # The couple's take-up draw is the gaining spouse's, the same draw
        # that decided take-up when the transfer was modelled on the
        # recipient alone.
        partner_would_claim = (
            partner(person("would_claim_marriage_allowance", period)) > 0
        )
        return chooses & partner_would_claim
