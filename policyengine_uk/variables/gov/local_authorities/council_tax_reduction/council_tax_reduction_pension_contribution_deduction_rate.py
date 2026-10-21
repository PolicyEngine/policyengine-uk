from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_england_pensioner_scheme,
    is_kingston_upon_thames_working_age,
    is_merton_working_age,
    is_newham_working_age,
    is_oxford_working_age,
    is_scotland_scheme,
    is_wales_scheme,
    is_westminster_working_age,
)


class council_tax_reduction_pension_contribution_deduction_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pension contribution deduction rate"
    documentation = (
        "The share of pension contributions deducted from earnings in the "
        "Council Tax Reduction means test, under the family's own scheme. "
        "Each scheme sets its own share, one-half in every scheme modelled: "
        "the England pensioner scheme (SI 2012/2885 Sch 1 paras 19 and 29), "
        "Wales (WSI 2013/3029 Sch 1 paras 13 and 23 and Sch 6 paras 15 and "
        "24), Scotland (SSI 2012/319 regs 33 and 36; SSI 2021/249 reg 50, and "
        "for the self-employed reg 51(9), which applies SSI 2012/303 regs 37 "
        "and 38) and the working-age schemes of Merton, Kingston upon Thames, "
        "Newham, Westminster and Oxford. None of them refers to Housing "
        "Benefit's share, so a reform of one scheme's share moves only that "
        "scheme. English working-age families outside those councils, whose "
        "reductions the model takes as reported, and families outside Great "
        "Britain, where there is no Council Tax Reduction, read the England "
        "default scheme's share (SI 2012/2886 Sch paras 42, 52 and 61). "
        "A working-age applicant with an award of Universal Credit is "
        "assessed instead on the Secretary of State's Universal Credit "
        "figures, which deduct relievable pension contributions in full "
        "(UC Regs 2013 reg 55(5)(a) for employed earnings and reg 57(2) step 4 "
        "for self-employed earnings): in Wales (WSI 2013/3029 Sch 6 para 9), "
        "Scotland (SSI 2021/249 regs 49(6)(a) and 51(2)) and Oxford (its "
        "scheme's Appendix 3). Welsh and Scottish working-age applicants "
        "with Universal Credit take that route "
        "(council_tax_reduction_devolved_working_age), so the share here "
        "reaches only those without it. Oxford has no such route yet (#2520), "
        "so the share reaches its Universal Credit applicants too. Merton, "
        "Kingston upon Thames, Newham and Westminster already assess them on "
        "Universal Credit income (_legacy.py)."
    )
    definition_period = YEAR
    unit = "/1"
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/19",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/29",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/52",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/15",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/33",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/50",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
    )

    def formula(benunit, period, parameters):
        la = parameters(period).gov.local_authorities
        household = benunit.household
        country = household("country", period)
        local_authority = household("local_authority", period)
        # The scheme follows the applicant's own family (SI 2012/2885 reg 3),
        # as in simulated_council_tax_reduction_benunit.
        has_pensioner = benunit("council_tax_reduction_pensioner", period)

        def rate(ctr):
            return ctr.means_test.pension_contribution_deduction_rate

        return select(
            [
                is_england_pensioner_scheme(country, has_pensioner),
                is_scotland_scheme(country),
                is_wales_scheme(country),
                is_merton_working_age(local_authority, country, has_pensioner),
                is_kingston_upon_thames_working_age(
                    local_authority, country, has_pensioner
                ),
                is_newham_working_age(local_authority, country, has_pensioner),
                is_westminster_working_age(local_authority, country, has_pensioner),
                is_oxford_working_age(local_authority, country, has_pensioner),
            ],
            [
                rate(la.england.council_tax_reduction.pensioners),
                rate(la.scotland.council_tax_reduction),
                rate(la.wales.council_tax_reduction),
                rate(la.merton.council_tax_reduction),
                rate(la.kingston_upon_thames.council_tax_reduction),
                rate(la.newham.council_tax_reduction),
                rate(la.westminster.council_tax_reduction),
                rate(la.oxford.council_tax_reduction),
            ],
            default=rate(la.england.council_tax_reduction.default_scheme),
        )
