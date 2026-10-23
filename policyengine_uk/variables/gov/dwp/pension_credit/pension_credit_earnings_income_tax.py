from policyengine_uk.model_api import *
from policyengine_uk.utils.pension_credit import employed_earnings_sources

DECISION = (
    "PolicyEngine does not model PAYE codes, so which part of a person's "
    "income tax is payable on their earnings is a methodology choice, put to "
    "Max on PolicyEngine/policyengine-uk#2019 and settled as option (a): treat "
    "earnings as the top slice of the person's income. "
)


def income_tax_with_inputs_zeroed(simulation, period, variables):
    """Each person's income tax with every person's value of each of
    ``variables`` set to nil, on a branch that is dropped afterwards."""
    return person_variable_with_inputs_zeroed(
        simulation, period, variables, "income_tax"
    )


def person_variable_with_inputs_zeroed(simulation, period, variables, output):
    """Each person's ``output`` with every person's value of each of
    ``variables`` set to nil, on a branch that is dropped afterwards."""
    name = "pension_credit_without_" + "_and_".join(variables)
    while name in simulation.branches or name == simulation.branch_name:
        name += "_"
    branch = simulation.get_branch(name)
    try:
        # Preserve every explicit stored input, including formula overrides
        # supplied through set_input after the simulation was constructed.
        branch.drop_computed_arrays()
        people = branch.populations["person"]
        for variable in variables:
            branch.set_input(variable, period, np.zeros(people.count))
        return people(output, period)
    finally:
        del simulation.branches[name]


class pension_credit_income_tax_without_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Income tax without employed earnings, for Pension Credit"
    documentation = (
        "The person's income tax if nobody in the simulation had employed "
        "earnings: employment income and the statutory sick, maternity and "
        "paternity pay that SPC Regs 2002 reg. 17A(2) counts as earnings. " + DECISION
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        income_tax = person("income_tax", period)
        sources = employed_earnings_sources(parameters, period)
        if not any((person(source, period) != 0).any() for source in sources):
            return income_tax
        return income_tax_with_inputs_zeroed(person.simulation, period, sources)


class pension_credit_income_tax_without_earnings(Variable):
    value_type = float
    entity = Person
    label = "Income tax without earnings, for Pension Credit"
    documentation = (
        "The person's income tax if nobody in the simulation had employed "
        "earnings (employment income and statutory sick, maternity and "
        "paternity pay) or self-employment income. " + DECISION
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        without_employment = person(
            "pension_credit_income_tax_without_employment_income", period
        )
        if not (person("self_employment_income", period) != 0).any():
            return without_employment
        return income_tax_with_inputs_zeroed(
            person.simulation,
            period,
            employed_earnings_sources(parameters, period) + ["self_employment_income"],
        )


class pension_credit_employment_income_tax(Variable):
    value_type = float
    entity = BenUnit
    label = "Income tax on employed earnings, for Pension Credit"
    documentation = (
        "The income tax payable on the claimant's and partner's employed "
        "earnings (employment income and statutory sick, maternity and "
        "paternity pay), which SPC Regs 2002 reg. 17(10) disregards in their "
        "net amount: the fall in the claimant's and partner's income tax "
        "without anyone's employed earnings, never negative. It includes any tax the "
        "earnings add on savings and dividends (a lost starting-rate band or "
        "personal savings allowance) and any effect of one partner's earnings "
        "on the other's tax (through the marriage allowance), so Pension "
        "Credit income does not change with either partner's earnings while "
        "the disregard covers them, provided the zero floor on net earnings "
        "does not limit the pension-contribution deduction. " + DECISION
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17A",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        added = person("income_tax", period) - person(
            "pension_credit_income_tax_without_employment_income", period
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        return max_(0, benunit.sum(added * claimant_or_partner))


class pension_credit_self_employment_income_tax(Variable):
    value_type = float
    entity = BenUnit
    label = "Income tax actually payable on self-employed profit, for Pension Credit"
    documentation = (
        "The income tax the claimant's and partner's self-employment income "
        "adds to their income tax, beneath any employed earnings: the fall in "
        "their income tax without anyone's employed earnings when nobody has "
        "self-employment income either, never negative. Pension Credit income "
        "replaces it with the notional tax of the Computation of Earnings "
        "Regulations 1996 reg. 14 (SPC Regs 2002 reg. 17(11)). " + DECISION
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17"

    def formula(benunit, period, parameters):
        person = benunit.members
        added = person(
            "pension_credit_income_tax_without_employment_income", period
        ) - person("pension_credit_income_tax_without_earnings", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        return max_(0, benunit.sum(added * claimant_or_partner))


class pension_credit_uncounted_income_tax_without_earnings(Variable):
    value_type = float
    entity = Person
    label = "Income tax on income Pension Credit does not count, without earnings"
    documentation = (
        "The part of the person's income tax, if nobody in the simulation had "
        "employment or self-employment income, that is not tax on income "
        "Pension Credit takes into account: the tax on rent from property, "
        "interest and dividends, and the Step 7 charges "
        "(legacy_means_test_income_tax). SPC Regs 2002 reg. 17(10)(a) "
        "disregards tax only on income taken into account, and Schedule IV "
        "paragraph 18 disregards actual income from capital, so Pension "
        "Credit income does not deduct this tax. It is measured without "
        "earnings because the tax on earnings is the extra tax the earnings "
        "cause, including on savings and dividends "
        "(pension_credit_employment_income_tax and "
        "pension_credit_self_employment_income_tax), which Pension Credit "
        "income does deduct. " + DECISION
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/17",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IV",
    )

    def formula(person, period, parameters):
        income_tax = person("pension_credit_income_tax_without_earnings", period)
        has_earnings = (person("employment_income", period) != 0) | (
            person("self_employment_income", period) != 0
        )
        if not has_earnings.any():
            counted = person("legacy_means_test_income_tax", period)
        else:
            counted = person_variable_with_inputs_zeroed(
                person.simulation,
                period,
                ["employment_income", "self_employment_income"],
                "legacy_means_test_income_tax",
            )
        return max_(0, income_tax - counted)
