from policyengine_uk.model_api import *


class housing_benefit_attained_pension_age_before_cutoff(Variable):
    value_type = bool
    entity = BenUnit
    label = "a member attained State Pension age before the Housing Benefit cutoff"
    documentation = (
        "Whether any member of the benefit unit attained State Pension age "
        "before the pension-age cutoff (1 April 2021). Such units keep the "
        "higher pension-age personal allowance; units whose members all "
        "attained it on or after the cutoff get the lower one. Before the "
        "cutoff took effect there was a single pension-age allowance, the "
        "higher one, so this is true for every unit then."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2021/188/regulation/2/made",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4",
    )

    def formula(benunit, period, parameters):
        cutoff = parameters(
            period
        ).gov.dwp.housing_benefit.allowances.pension_age_cutoff
        if cutoff is None:
            return np.ones(benunit.count, dtype=bool)
        # "Pensionable age" is State Pension age under Pensions Act 1995 Sch 4
        # para 1 (SSCBA 1992 s.122(1), applied to these regulations by the
        # Interpretation Act 1978 s.11), which state_pension_age_date follows.
        #
        # Para 1(2)(b) keeps the higher couple rate where "one member or both
        # members" attained pensionable age before the cutoff, and (2)(c) gives
        # the lower one where "both members" attained it on or after. Neither
        # covers a couple where one member has not reached it and the other did
        # so after the cutoff. In law that couple cannot be on pension-age
        # Housing Benefit: mixed-age couples keep it only under the savings for
        # awards from before 15 May 2019 (SI 2019/37 art 4), when the older
        # member had already reached it. PolicyEngine can still give such a
        # unit pension-age rates through a reported continuing award; it gets
        # the lower rate, since the explanatory note to SI 2021/188 keeps the
        # uplift only where "one or more members ... attained pensionable age
        # before 1st April 2021".
        #
        # Dates are compared as YYYYMMDD integers, which are exact; as float32
        # they would not be (20210401 would round to 20210400).
        attained = benunit.members("state_pension_age_date", period)
        return benunit.any(attained < cutoff)
