"""Who the benefit cap reads, for the Universal Credit and Housing Benefit caps."""

from policyengine_core.model_api import where


def benefit_cap_couple(benunit, period):
    """The single person or couple whose benefits and circumstances the cap reads.

    The model applies one cap to Universal Credit and Housing Benefit, and
    each scheme names its own couple. For a family on Universal Credit it is
    the claimants, the members of the couple whose income the award assesses
    (is_uc_assessed_claimant): a single claimant or joint claimants, and the
    other member of a couple where one member claims as a single person
    (UC Regs 2013 reg 78(2)). Otherwise it is Housing Benefit's claimant and
    partner (is_claimant_or_partner; HB Regs 2006 regs 2(1), 75A). The two
    are the same unless is_uc_claimant is entered.
    """
    person = benunit.members
    on_universal_credit = benunit("universal_credit_pre_benefit_cap", period) > 0
    return where(
        benunit.project(on_universal_credit),
        person("is_uc_assessed_claimant", period),
        person("is_claimant_or_partner", period),
    )
