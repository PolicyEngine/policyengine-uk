from policyengine_uk.model_api import *


class council_tax_reduction_claimant_benunit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Family claims Council Tax Reduction for the household"
    documentation = (
        "Whether this family can claim Council Tax Reduction on the "
        "household's council tax. Only a person liable to pay the council tax "
        "is in a class entitled to a reduction. Where the household's rent is "
        "shared, every family liable for it is jointly and severally liable "
        "for the council tax and claims on its part. Otherwise the household "
        "head's family claims: the head is the household reference person, a "
        "householder in whose name the accommodation is owned or rented, and "
        "so the liable resident. Other families in the household are not "
        "liable and cannot claim, whatever their ages."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/75",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/22",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/24",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/13",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/14",
    )

    def formula(benunit, period, parameters):
        # A family liable for a share of the rent is jointly and severally
        # liable for the council tax with the head's family (s.6(3), s.75(3)).
        head_family = benunit("benunit_contains_household_head", period)
        sharer = benunit("liable_for_share_of_household_rent", period)
        return head_family | sharer
