from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import stored_as_input
from policyengine_uk.utils.trading_allowance import trading_allowance_reliefs

DEDUCTIONS = (
    "trading_allowance_deduction",
    "miscellaneous_income_trading_allowance_deduction",
)


class uses_trading_allowance(Variable):
    value_type = bool
    entity = Person
    label = "Uses the trading allowance"
    documentation = (
        "Whether the person takes the trading allowance for the year, by full "
        "or partial relief, rather than ordinary treatment: the allowance "
        "relieves their trade profits or their income not otherwise charged. "
        "Either relief covers all their relevant income (ITTOIA 2005 s. 783A), "
        "so it makes every relevant trade's current profit or loss its "
        "allowance figure (ss. 783AF and 783AI), and a current trading loss "
        "cannot then be claimed. A person with a larger current loss takes "
        "ordinary treatment and claims it: within the allowance by electing "
        "out of full relief (s. 783AL), above it by not electing for partial "
        "relief (s. 783AM). A claimant in the input data "
        "(trading_allowance_claim_status) counts whenever they take it, even "
        "where it relieves nothing beyond their input profit. By default, "
        "with no current loss, they take it at any allowance at or above the "
        "one their profit already deducts. That is the deductions' own "
        "election, so it counts only where both come from their formulas: "
        "where either is an input (supplied, or set by the model) or "
        "neutralised, the deductions applied are not the election's, and "
        "only a positive one counts, for a claimant as for anyone. A reform "
        "that replaces either deduction's formula should replace this one's "
        "too."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783A",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783A",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AL",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AL",
        ),
        dict(
            title="Income Tax (Trading and Other Income) Act 2005 s. 783AM",
            href="https://www.legislation.gov.uk/ukpga/2005/5/section/783AM",
        ),
    ]

    def formula(person, period, parameters):
        uses = (person("trading_allowance_deduction", period) > 0) | (
            person("miscellaneous_income_trading_allowance_deduction", period) > 0
        )
        # A claimant with a profit can take the allowance with a deduction
        # of nil or less. Only the deductions' formulas make that election,
        # so it counts only where the deductions applied are theirs. Without
        # such a claimant there is nothing to add, and the reliefs are not
        # worked out a third time.
        status = person("trading_allowance_claim_status", period)
        claimant = (status == status.possible_values.CLAIMANT) & (
            person("self_employment_income", period) > 0
        )
        system = person.simulation.tax_benefit_system
        if not claimant.any() or any(
            system.get_variable(name).is_neutralized
            or stored_as_input(person, name, period)
            for name in DEDUCTIONS
        ):
            return uses
        _, _, claimant_takes_allowance = trading_allowance_reliefs(
            person, period, parameters
        )
        return uses | claimant_takes_allowance
