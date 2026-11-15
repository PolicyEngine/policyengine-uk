from policyengine_uk.model_api import *


def child_disability_premium_benefit_conditions(person, period):
    """The disabled child and enhanced disability premium conditions that
    Housing Benefit and pension-age Council Tax Reduction share, for each
    person, leaving out the armed forces independence payment.

    A child or young person meets the disabled child condition with a positive
    DLA amount (either component), a positive PIP amount (either component) or
    the blindness indicator (HB Regs 2006 Sch 3 para 16; SI 2012/2885 Sch 2
    para 8(a)-(b); WSI 2013/3029 Sch 2 para 8(a)-(b); SSI 2012/319 Sch 1 para
    9(a)-(b)). They meet the enhanced condition with the DLA care component at
    the highest rate (has_highest_dla_sc_award) or the PIP daily living
    component at the enhanced rate (has_enhanced_pip_dl_award) (HB Regs 2006
    Sch 3 para 15; SI 2012/2885 Sch 2 para 7(1)(a)-(b); WSI 2013/3029 Sch 2
    para 7(1)(a)-(b); SSI 2012/319 Sch 1 para 8(1)(a)-(b)). Each caller adds
    its own armed forces independence payment route.

    Neither condition reads a field for child disability payment or adult
    disability payment, which the model lacks, so callers enter those awards
    in the DLA and PIP fields.
    """
    dla = (person("dla_sc", period) > 0) | (person("dla_m", period) > 0)
    pip = (person("pip_dl", period) > 0) | (person("pip_m", period) > 0)
    disabled_child = dla | pip | person("is_blind", period)
    enhanced = person("has_highest_dla_sc_award", period) | person(
        "has_enhanced_pip_dl_award", period
    )
    return disabled_child, enhanced
