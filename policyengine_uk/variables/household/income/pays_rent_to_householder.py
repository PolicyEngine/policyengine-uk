from policyengine_uk.model_api import *


class pays_rent_to_householder(Variable):
    value_type = bool
    entity = Person
    label = "in a family that pays the householder rent as boarders or lodgers"
    documentation = (
        "Whether this person's benefit unit, which does not contain the "
        "household head, pays the household head rent for board and lodging "
        "or for lodging. Such a person is liable to make payments on a "
        "commercial basis for their occupation, so is not a non-dependant of "
        "the householder. The model takes every such payment to be commercial "
        "and the payer not to be a close relative living there, whom the "
        "rules keep as a non-dependant (HB reg 3(3) with reg 9(1); CTR reg "
        "9(3)). The Family Resources Survey asks about this rent only for "
        "people not related to the household reference person."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
    ]

    def formula(person, period, parameters):
        paid = add(person, period, ["rent_paid_as_boarder", "rent_paid_as_lodger"])
        in_head_benunit = person.benunit.any(person("is_household_head", period))
        return person.benunit.any(paid > 0) & ~in_head_benunit
