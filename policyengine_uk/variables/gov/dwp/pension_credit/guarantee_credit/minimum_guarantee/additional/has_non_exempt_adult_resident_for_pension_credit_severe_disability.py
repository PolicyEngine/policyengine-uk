from policyengine_uk.model_api import *


class has_non_exempt_adult_resident_for_pension_credit_severe_disability(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Has an adult resident who bars the Pension Credit severe disability addition"
    )
    documentation = (
        "Whether someone aged 18 or over, other than the claimant or partner "
        "and other than a person whose presence SPC Regs 2002 Sch. I para. 2 "
        "ignores, normally resides with the claimant or partner. A person "
        "resides with another if they share any accommodation except a "
        "bathroom, a lavatory or a communal area (Sch. I para. 3(1)). Households "
        "built from the Family Resources Survey follow its definition: people "
        "at the same address who share cooking facilities and a living room, "
        "sitting room or dining area. They share more than a bathroom, lavatory "
        "or communal area, so every other household member is treated as "
        "residing with the claimant. People who share accommodation with the "
        "claimant without belonging to the same household, such as sharers of "
        "only a kitchen, are not seen."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/3",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        non_exempt_adult = person(
            "is_non_exempt_adult_resident_for_pension_credit_severe_disability",
            period,
        )
        in_household = benunit.max(person.household.sum(non_exempt_adult))
        # The claimant and partner do not reside "with" themselves.
        claimant_or_partner = person("is_claimant_or_partner", period)
        own_claimant_or_partner = benunit.sum(non_exempt_adult & claimant_or_partner)
        return in_household > own_claimant_or_partner
