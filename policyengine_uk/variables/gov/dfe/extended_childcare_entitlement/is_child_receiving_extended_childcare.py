from policyengine_uk.model_api import *


class is_child_receiving_extended_childcare(Variable):
    value_type = bool
    entity = Person
    label = "child is receiving extended childcare entitlement"
    documentation = (
        "Whether this child gets working parent hours beyond any universal or "
        "targeted hours it gets. A 3- or 4-year-old who gets the universal "
        "hours, in a family using no more than 15 hours a week, is on the "
        "universal entitlement only. Nobody receives it when the family's "
        "extended_childcare_entitlement is zero; a positive family amount "
        "supplied as an input, with no working parent hours calculated for "
        "any child, counts for every qualifying child of an eligible age."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        benunit = person.benunit
        family_amount = benunit("extended_childcare_entitlement", period)

        # Calculated amounts: each child's own working parent hours.
        child_amount = person("extended_childcare_entitlement_per_child", period)
        calculated_family_amount = benunit.sum(child_amount)

        # A supplied family amount that no child's calculated hours account
        # for: attribute it to every qualifying child with hours at its age.
        p = parameters(period).gov.dfe.extended_childcare_entitlement
        qualifying_child = person(
            "extended_childcare_entitlement_qualifying_child", period
        ) & (p.hours.calc(person("age", period)) > 0)
        supplied_only = benunit.project(calculated_family_amount) <= 0

        return (benunit.project(family_amount) > 0) & (
            (child_amount > 0) | (supplied_only & qualifying_child)
        )
