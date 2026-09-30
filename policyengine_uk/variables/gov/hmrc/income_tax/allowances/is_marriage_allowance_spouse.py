from policyengine_uk.model_api import *


class is_marriage_allowance_spouse(Variable):
    value_type = bool
    entity = Person
    label = "Spouse or civil partner for Marriage Allowance"
    documentation = (
        "Whether this person is one of the married couple or civil partners "
        "in their benefit unit, who can make or gain from a Marriage "
        "Allowance election. These are the two eldest members whose marital "
        "status is married, and only when the benefit unit has two. The Act "
        "needs only a marriage or civil partnership, not living together, but "
        "a spouse outside the benefit unit is not modelled."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 55C(1)(a)",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/55C",
    )

    def formula(person, period, parameters):
        status = person("marital_status", period)
        married = status == status.possible_values.MARRIED
        # Without a marital status input, every member of a married benefit
        # unit, children included, is married; the two eldest are the couple.
        rank = person.get_rank(
            person.benunit, -person("age", period), condition=married
        )
        spouse = married & (rank < 2)
        return spouse & (person.benunit.sum(spouse) == 2)
