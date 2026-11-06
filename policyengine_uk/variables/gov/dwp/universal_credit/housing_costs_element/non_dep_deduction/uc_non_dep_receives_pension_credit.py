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
        "their Universal Credit housing element. Results for families liable "
        "for the household's rent (benunit_is_liable_for_household_rent) are "
        "disregarded because none of their members is a non-dependant. A "
        "boarder's or lodger's family is not ruled out: its non-paying adult "
        "members can be non-dependants, and keep the exemption when the "
        "family receives Pension Credit. For that family the branch fixes "
        "the family's Universal Credit housing element, which may cover the "
        "rent it pays the householder, at nil, and computes its Pension "
        "Credit there. A family whose members are all over the qualifying "
        "age claims no Universal "
        "Credit, so the branch gives its actual Pension Credit."
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
        # the earnings counterfactuals on the parent so this branch and
        # ordinary Pension Credit share them whichever is requested first.
        benunit.members("pension_credit_income_tax_without_earnings", period)
        benunit.members(
            "legacy_means_test_uncounted_income_tax_without_earnings", period
        )
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
        # A boarder's or lodger's family still has a non-paying member who can
        # be a non-dependant, so only liability for the household's rent
        # rules the family out here.
        return (pension_credit > 0) & ~benunit(
            "benunit_is_liable_for_household_rent", period
        )
