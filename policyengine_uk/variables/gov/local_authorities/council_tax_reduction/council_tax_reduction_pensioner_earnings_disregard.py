from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


class council_tax_reduction_pensioner_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction pensioner earnings disregard"
    documentation = (
        "Sums disregarded from the net earnings of a pension-age applicant and "
        "partner under the national Council Tax Reduction rules for "
        "pensioners in England, Wales and Scotland. A lone parent has £25 a "
        "week, an applicant with a partner £10 and anyone else £5, capped at "
        "net earnings. The additional earnings disregard of £17.10 (£37.10 "
        "in Scotland from 6 April 2020 to 4 April 2021) is added where a work "
        "condition is met and net earnings at least equal the other "
        "disregards and the additional amount. The amounts and work "
        "conditions are those of the Housing Benefit pension-age schedule "
        "(SI 2006/214 Sch 4), and an employee's actual earnings have the same "
        "deductions (SI 2012/2885 Sch 1 para 19, WSI 2013/3029 Sch 1 para "
        "13, SSI 2012/319 reg 33), so the Housing Benefit net earnings and "
        "work conditions are used. The notional tax on estimated earnings "
        "and on self-employed profit can differ (Scotland deducts only the "
        "personal allowance, SSI 2012/319 regs 33(4) and 37(1)); the model "
        "applies the Housing Benefit approximation to all of them. The earnings test leaves out "
        "childcare charges, which the model does not deduct from Council Tax "
        "Reduction income. The £20 "
        "disregards for disabled people, carers and some part-time "
        "occupations, and the exempt work disregard, are not modelled. Zero "
        "for families that are not the schemes' pensioners "
        "(council_tax_reduction_pensioner), whose schemes are local in "
        "England and have their own schedules in Wales and Scotland, and "
        "outside Great Britain."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/4",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/19",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/13",
        "https://www.legislation.gov.uk/ssi/2012/319/schedule/2",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/33",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.local_authorities
        england = p.england.council_tax_reduction.pensioners.earnings_disregard
        wales = p.wales.council_tax_reduction.pensioners.earnings_disregard
        scotland = p.scotland.council_tax_reduction.pensioners.earnings_disregard
        country = benunit.household("country", period)
        in_england = country == Country.ENGLAND
        in_wales = country == Country.WALES
        in_scotland = country == Country.SCOTLAND

        def national(amount):
            return select(
                [in_wales, in_scotland],
                [wales[amount], scotland[amount]],
                default=england[amount],
            )

        net_earnings = benunit("housing_benefit_net_earnings", period)
        # SI 2012/2885 Sch 4 paras 2 and 8; WSI 2013/3029 Sch 3 paras 2 and 8;
        # SSI 2012/319 Sch 2 paras 2 and 8. A lone parent has £25 in all,
        # not £25 plus para 8's £5, as for Housing Benefit.
        weekly_amount = select(
            [benunit("is_lone_parent", period), benunit("is_couple", period)],
            [national("lone_parent"), national("couple")],
            default=national("single"),
        )
        standard = min_(weekly_amount * WEEKS_IN_YEAR, net_earnings)
        # Para 10 in each: the additional earnings disregard.
        additional_amount = national("additional") * WEEKS_IN_YEAR
        # "Equal or exceed", compared in pence: net earnings are float32.
        covers_additional = np.round(net_earnings.astype(float), 2) >= np.round(
            (standard + additional_amount).astype(float), 2
        )
        additional = where(
            benunit(
                "meets_housing_benefit_additional_earnings_disregard_conditions", period
            )
            & covers_additional,
            additional_amount,
            0,
        )
        # The pensioner schedules apply to the schemes' pensioners: the
        # qualifying age for State Pension Credit, and no income-related
        # benefit or Universal Credit award (SI 2012/2885 reg 3; WSI
        # 2013/3029 reg 3; SSI 2012/319 reg 12).
        pensioner = benunit("council_tax_reduction_pensioner", period)
        in_great_britain = in_england | in_wales | in_scotland
        return where(pensioner & in_great_britain, standard + additional, 0)
