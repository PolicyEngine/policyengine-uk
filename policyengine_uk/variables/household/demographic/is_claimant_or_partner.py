from policyengine_uk.model_api import *


class is_claimant_or_partner(Variable):
    """The single adult or couple a benefit unit is formed around.

    In benefit law this is the claimant and their partner, as opposed to the
    children and young persons they are responsible for (SSCBA 1992
    s.137(1) "family"; WRA 2012 ss.39-40; SPCA 2002 s.17; TCA 2002 s.3).
    The same two people are the spouses or civil partners for income tax
    purposes when the benefit unit is a married couple.

    Benefit units follow the Family Resources Survey definition: a single
    adult or a couple plus any dependent children. So the claimant and
    partner are the benefit unit's adults under that definition, which is
    the HBAI one (`is_hbai_adult`). Each programme applies its own age and
    other conditions to them.
    """

    value_type = bool
    entity = Person
    label = "Claimant or partner"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/137",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/39",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/17",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
    )

    def formula(person, period, parameters):
        return person("is_hbai_adult", period)
