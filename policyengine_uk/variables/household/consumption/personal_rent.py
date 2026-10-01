from policyengine_uk.model_api import *


class personal_rent(Variable):
    value_type = float
    entity = Person
    label = "Rent liable"
    documentation = (
        "The rent this person is liable for: an equal share of the "
        "household's rent among the people liable for it, plus anything this "
        "person pays the householder as a boarder or lodger. Where the "
        "household head's family is the only one liable, its claimant and "
        "partner share the whole rent, so the family's total is the "
        "household's rent."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/24",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12B",
    )

    def formula(person, period, parameters):
        # Where people in more than one family are liable for the same rent,
        # each person's core rent is the total divided by the number of
        # people liable (UC Regs 2013 Sch 4 para 24(4): A / B x C), which also
        # apportions Housing Benefit eligible rent by the number of people
        # liable (HB Regs 2006 reg 12B(4)).
        rent = person.household("rent", period)
        liable = person("is_liable_for_household_rent", period)
        liable_people = person.household.sum(liable)
        # A household with nobody marked liable (for example a head who is
        # not a claimant or partner) leaves the rent with the household head.
        head = person("is_household_head", period)
        heads = person.household.sum(head)
        share = where(
            liable_people > 0,
            liable / max_(liable_people, 1),
            head / max_(heads, 1),
        )
        # A licence or other permission to occupy is a rent payment (UC Regs
        # 2013 Sch 1 para 2(b); HB Regs 2006 reg 12(1)): boarders and lodgers
        # are liable for what they pay the householder.
        paid_to_householder = add(
            person, period, ["rent_paid_as_boarder", "rent_paid_as_lodger"]
        )
        return rent * share + paid_to_householder
