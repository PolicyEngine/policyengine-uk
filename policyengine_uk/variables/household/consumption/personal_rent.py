from policyengine_uk.model_api import *


class personal_rent(Variable):
    value_type = float
    entity = Person
    label = "Rent liable"
    documentation = (
        "The rent this person is liable for. Each family's share of the "
        "household's rent (see share_of_household_rent) sits on one person: "
        "the household head for the household head's family, otherwise the "
        "family's head. Anything a person pays the householder as a boarder "
        "or lodger is their own. Where the household head's family is the "
        "only one liable, the household head carries the whole rent."
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
        rent = person.household("rent", period)
        share = person.benunit("share_of_household_rent", period)
        household_head = person("is_household_head", period)
        head_family = person.benunit.any(household_head)
        holder = where(head_family, household_head, person("is_benunit_head", period))
        # A licence or other permission to occupy is a rent payment (UC Regs
        # 2013 Sch 1 para 2(b); HB Regs 2006 reg 12(1)): boarders and lodgers
        # are liable for what they pay the householder.
        paid_to_householder = add(
            person, period, ["rent_paid_as_boarder", "rent_paid_as_lodger"]
        )
        return rent * share * holder + paid_to_householder
