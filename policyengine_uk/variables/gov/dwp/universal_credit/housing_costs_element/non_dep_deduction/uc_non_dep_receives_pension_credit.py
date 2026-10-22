from policyengine_uk.model_api import *


class uc_non_dep_receives_pension_credit(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Non-rent-liable family receives Pension Credit for UC housing contributions"
    )
    documentation = (
        "Whether a family not liable for rent receives Pension Credit, for the "
        "Universal Credit non-dependant housing contribution exemption. Such "
        "a family's own Universal Credit housing element is zero. Calculating "
        "its Pension Credit in a branch with that element fixed at zero "
        "therefore preserves its entitlement, including legacy-closure "
        "routing, take-up, explicit inputs and frozen Pension Credit reforms. "
        "It avoids evaluating a renter's own Pension Credit while calculating "
        "their Universal Credit housing element. Rent-liable families' "
        "branch results are disregarded because they are not non-dependants."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/16",
    )

    def formula(benunit, period, parameters):
        # A non-dependant is not liable for the rent (Sch 4 para 9(2)(d)),
        # so their own housing element is already zero. This branch keeps
        # their actual Pension Credit calculation while breaking the cycle
        # through the renter's UC entitlement and pension-age route.
        simulation = benunit.simulation
        # Income tax is independent of the UC housing element. Calculate
        # both earnings counterfactuals on the parent so this branch and
        # ordinary Pension Credit share them whichever is requested first.
        benunit.members("pension_credit_income_tax_without_earnings", period)
        name = "uc_non_dep_pension_credit"
        while name in simulation.branches or name == simulation.branch_name:
            name += "_"
        branch = simulation.get_branch(name)
        try:
            branch.set_input(
                "uc_housing_costs_element", period, np.zeros(benunit.count)
            )
            pension_credit = branch.calculate("pension_credit", period)
        finally:
            # A later period or changed input must start from current inputs.
            del simulation.branches[name]
        return (pension_credit > 0) & ~benunit("benunit_is_rent_liable", period)
