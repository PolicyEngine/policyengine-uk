from policyengine_uk.model_api import *


class council_tax_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Benefit"
    documentation = (
        "A family that claims gets the simulated reduction where the model "
        "simulates its own scheme, and its reported reduction otherwise. A "
        "claimant jointly liable with others can get at most its own share "
        "of the council tax, so its reported reduction is limited to that "
        "share. A family that cannot claim keeps a reported reduction only "
        "where no claim in its household is simulated."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/7",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/2",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/4",
    )

    def formula(benunit, period, parameters):
        supported = benunit("council_tax_reduction_scheme_supported", period)
        simulated = benunit("simulated_council_tax_reduction_benunit", period)
        reported = benunit("council_tax_benefit_reported", period)
        claimant = benunit("council_tax_reduction_claimant_benunit", period)
        share = benunit("council_tax_reduction_joint_liability_share", period)
        # SI 2012/2885 Sch 1 para 7(3)-(4): a jointly liable claimant's
        # maximum reduction is on its share of the council tax.
        share_of_liability = (
            benunit.household(
                "council_tax_reduction_maximum_eligible_liability", period
            )
            * share
        )
        reported_claim = where(share < 1, min_(reported, share_of_liability), reported)
        household_simulates = benunit.household(
            "council_tax_reduction_household_has_simulated_claim", period
        )
        not_claiming = where(household_simulates, 0, reported)
        return where(
            claimant, where(supported, simulated, reported_claim), not_claiming
        )
