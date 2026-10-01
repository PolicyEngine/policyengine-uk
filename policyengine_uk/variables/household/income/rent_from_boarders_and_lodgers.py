from policyengine_uk.model_api import *


class rent_from_boarders_and_lodgers(Variable):
    value_type = float
    entity = Person
    label = "rent received from boarders and lodgers"
    documentation = (
        "Rent the household head receives from boarders and lodgers: the "
        "rent paid as a boarder or lodger by household members outside the "
        "head's benefit unit, shared equally where more than one person is "
        "flagged as household head. The Family Resources Survey records this "
        "rent only on the payer. It is a transfer within the household, so "
        "household income measures do not include it; it enters income tax "
        "as rent-a-room receipts and the legacy means tests through the "
        "home-letting income."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        paid = add(person, period, ["rent_paid_as_boarder", "rent_paid_as_lodger"])
        head = person("is_household_head", period)
        in_head_benunit = person.benunit.any(head)
        paid_to_head = person.household.sum(paid * ~in_head_benunit)
        heads = person.household.sum(head)
        return where(head, paid_to_head / max_(heads, 1), 0)
