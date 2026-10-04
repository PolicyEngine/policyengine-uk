from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


class council_tax_reduction_working_age_adult_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction adult premiums"
    documentation = (
        "Annual disability, severe disability, enhanced disability and carer "
        "premiums in a working-age applicable amount in Scotland or Wales, at "
        "each country's own amounts. Who qualifies follows the model's "
        "legacy-benefit premium variables (disability_premium, "
        "enhanced_disability_premium, severe_disability_premium), including "
        "whether the severe disability premium is at the single or couple "
        "rate. The carer premium is paid for each qualifying claimant or "
        "partner. The employment and support allowance components, and the "
        "disability premium's exclusion for limited capability for work, are "
        "not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/17",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/7/paragraph/17",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.local_authorities
        scotland = is_scotland_scheme(benunit.household("country", period))
        scot = p.scotland.council_tax_reduction.working_age.adult_premiums
        wales = p.wales.council_tax_reduction.working_age.adult_premiums
        dwp = parameters(period).gov.dwp.disability_premia

        def amount(node, field=None):
            s = getattr(scot, node)
            w = getattr(wales, node)
            if field is not None:
                s, w = getattr(s, field), getattr(w, field)
            return where(scotland, s, w)

        couple = benunit("is_couple", period)
        disability = benunit("disability_premium", period) > 0
        enhanced = benunit("enhanced_disability_premium", period) > 0
        severe_weekly = benunit("severe_disability_premium", period) / WEEKS_IN_YEAR
        severe = severe_weekly > 0
        # The legacy variable pays either the single or the double rate;
        # follow whichever it chose.
        severe_double = severe_weekly > (dwp.severe_single + dwp.severe_couple) / 2
        weekly = (
            disability
            * where(
                couple,
                amount("disability_premium", "couple"),
                amount("disability_premium", "single"),
            )
            + enhanced
            * where(
                couple,
                amount("enhanced_disability_premium", "couple"),
                amount("enhanced_disability_premium", "single"),
            )
            + severe
            * where(
                severe_double,
                amount("severe_disability_premium", "couple"),
                amount("severe_disability_premium", "single"),
            )
            + benunit("council_tax_reduction_working_age_carers", period)
            * amount("carer_premium")
        )
        return weekly * WEEKS_IN_YEAR
