from policyengine_uk.model_api import *


class council_tax_reduction_claimant_benunit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Family claims Council Tax Reduction for the household"
    documentation = (
        "Whether this family can claim Council Tax Reduction on the "
        "household's council tax. Every class of person entitled to a "
        "reduction is limited to people liable to pay the council tax, and "
        "liability goes to the resident (aged 18 or over) with the greatest "
        "interest in the dwelling, jointly where several hold the same "
        "interest. The model takes the household head (the household "
        "reference person, a householder in whose name the accommodation is "
        "owned or rented) as that resident, and families liable for a share "
        "of the household's rent as jointly liable with the head's family. "
        "Other families are treated as not liable, whatever their ages. A "
        "family claims only if its claimant or partner is aged 18 or over. "
        "Joint owners in separate families, and dwellings where the owner "
        "rather than a resident is liable, are not identified."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/13A",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/75",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/99",
        "https://www.legislation.gov.uk/ukpga/1992/14/schedule/1A/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/16",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/21",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/22",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/23",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/24",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/25",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/13",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/14",
    )

    def formula(benunit, period, parameters):
        # A family liable for a share of the rent is jointly and severally
        # liable for the council tax with the head's family (s.6(3), s.75(3)).
        # Only a resident aged 18 or over can be liable (s.6(5), s.99(1)).
        person = benunit.members
        adult_claimant = benunit.any(
            person("is_claimant_or_partner", period) & (person("age", period) >= 18)
        )
        head_family = benunit("benunit_contains_household_head", period)
        sharer = benunit("liable_for_share_of_household_rent", period)
        return (head_family | sharer) & adult_claimant
