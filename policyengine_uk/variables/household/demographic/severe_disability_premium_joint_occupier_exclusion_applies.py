from policyengine_uk.model_api import *


class severe_disability_premium_joint_occupier_exclusion_applies(Variable):
    value_type = bool
    entity = BenUnit
    label = "Joint occupier exclusion established for severe disability premium"
    documentation = (
        "An explicit caller-provided statutory assertion for this benefit unit "
        "and year. True means that every other modelled rent-liable claimant "
        "or partner selected by is_liable_for_household_rent satisfies the "
        "applicable joint-occupier or separate-landlord-liability exclusions "
        "relative to this benefit unit, for every applicable programme using "
        "the shared legacy severe disability premium non-dependant test. "
        "This includes the Housing Benefit reg 3(3)/reg 9(1) conditions and "
        "the Income Support reg 3(2C) close-relative and liability/first-occupation "
        "history conditions where relevant. These references do not establish "
        "that every downstream programme has the same legal definition. "
        "False means the full assertion is not established: leave it false "
        "if facts are unknown, any selected person fails the conditions, or "
        "only a subset is known to qualify. False is not itself a statement "
        "that anyone is a non-dependant. Each benefit unit must supply its "
        "own assertion; another unit's assertion is not inherited. The model "
        "does not infer this input from rent, head status, family roles or "
        "liable_for_share_of_household_rent. The assertion is used only if "
        "this benefit unit itself has a modelled rent-liable claimant or "
        "partner. It removes only other modelled liable claimants or partners "
        "from this test, not every member of their family or a non-paying "
        "adult. Mixed qualifying and non-qualifying liable-person subsets "
        "cannot be represented by this single boolean. This input does not "
        "establish co-ownership, commercial arrangements, engaged-carer facts "
        "or broader programme eligibility, and does not certify all CTR, "
        "DfE or Northern Ireland legal coverage."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/3",
    )
