from policyengine_uk.model_api import *


class would_claim_marriage_allowance(Variable):
    label = "Would claim Marriage Allowance"
    documentation = (
        "Whether this person would claim Marriage Allowance from their spouse "
        "or civil partner's election when it lowers the couple's income tax. "
        "Generated stochastically in the dataset using take-up rates. The "
        "couple's election follows the value on the spouse who would gain "
        "(makes_marriage_allowance_election)."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True


class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = "Marriage Allowance received"
    documentation = (
        "The transferable amount this person's spouse or civil partner gives "
        "up under a Marriage Allowance election. This person's tax falls by "
        "the appropriate percentage of it (marriage_allowance_tax_reduction); "
        "the allowance itself does not come off their taxable income."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007 s. 55B",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55B",
        ),
        dict(
            title="Income Tax Act 2007 s. 55C",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/55C",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        # The gaining party is the other spouse or civil partner of the person
        # who elects (s. 55C(1)(a)); at most one of the couple elects.
        spouse = person("is_marriage_allowance_spouse", period)
        given_up = person("makes_marriage_allowance_election", period) * person(
            "marriage_allowance_transferable_amount", period
        )
        return spouse * (person.benunit.sum(spouse * given_up) - given_up)
