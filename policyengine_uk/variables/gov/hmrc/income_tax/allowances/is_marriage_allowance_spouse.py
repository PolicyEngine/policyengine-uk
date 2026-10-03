from policyengine_uk.model_api import *


class is_marriage_allowance_spouse(Variable):
    value_type = bool
    entity = Person
    label = "Spouse or civil partner for Marriage Allowance"
    documentation = (
        "Whether this person is one of the married couple or civil partners "
        "in their benefit unit, who can make or gain from a Marriage "
        "Allowance election: the claimant and partner of a married benefit "
        "unit, never a child in it. The Act needs only a marriage or civil "
        "partnership, not living together, but a spouse outside the benefit "
        "unit is not modelled."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 55C(1)(a)",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/55C",
    )

    def formula(person, period, parameters):
        status = person("marital_status", period)
        spouse = (status == status.possible_values.MARRIED) & person(
            "is_claimant_or_partner", period
        )
        return spouse & (person.benunit.sum(spouse) == 2)
