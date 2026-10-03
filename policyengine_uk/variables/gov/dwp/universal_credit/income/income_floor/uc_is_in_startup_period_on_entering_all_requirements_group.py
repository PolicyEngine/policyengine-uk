from policyengine_uk.model_api import *


class uc_is_in_startup_period_on_entering_all_requirements_group(Variable):
    value_type = bool
    entity = Person
    label = (
        "In a Universal Credit start-up period that began on entering the "
        "all work-related requirements group"
    )
    documentation = (
        "Whether the claimant is in the start-up period that begins when a "
        "self-employed claimant moves into the all work-related requirements "
        "group and is then first found to be in gainful self-employment. "
        "DWP cannot find a claimant in the no work-related requirements, "
        "work-focused interview or work preparation group to be gainfully "
        "self-employed; it holds a Gateway Interview after the move, and a "
        "start-up period runs for 12 months from the assessment period of "
        "that decision. The model sees the move of the responsible carer "
        "whose youngest child reaches the age for the all work-related "
        "requirements group (3 since 3 April 2017), and treats the 12 months "
        "as the year in which the child has that age. Other moves, such as "
        "the end of limited capability for work, are not dated in the data: "
        "set uc_is_in_startup_period, or this variable, for them. From 23 "
        "September 2020 an established trade qualifies; before then a "
        "start-up period needed a trade begun in the previous 12 months, "
        "which uc_is_in_startup_period covers. No start-up period applies "
        "where uc_startup_period_barred_by_earlier_floor_or_startup."
    )
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 63",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/63",
        ),
        dict(
            title="Welfare Reform Act 2012 ss. 21(1)(aa) and 22",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/21",
        ),
        dict(
            title="DWP, Self-employed and gainfully self-employed: Guidance, version 22.0 (deposited paper DEP2025-0769), pp. 3, 8-9 and 11",
            href="https://data.parliament.uk/DepositedPapers/Files/DEP2025-0769/153._Self-employed_and_gainfully_self-employed-Guidance_V22.0.pdf",
        ),
    ]
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit
        group = person("uc_work_related_group_apart_from_earnings", period)
        all_requirements = group == group.possible_values.ALL_REQUIREMENTS
        # The responsible carer leaves the lower groups when the youngest
        # child reaches the work preparation limit, the highest of the
        # child-age limits (s. 21(1)(aa); 3 since 3 April 2017, 5 before).
        entry_age = p.work_requirements.responsible_carer.child_age.work_preparation
        youngest = person.benunit("uc_youngest_child_age", period)
        # Reg. 63(1): 12 months from the assessment period of the gainful
        # self-employment decision, which DWP makes "as soon as possible
        # following the move". In a yearly model, the year in which the
        # youngest child has the entry age.
        entered_this_year = (
            person("uc_is_responsible_carer", period)
            & (youngest >= entry_age)
            & (youngest < entry_age + 1)
        )
        found_gainfully_self_employed = person(
            "uc_is_in_gainful_self_employment", period
        )
        barred = person("uc_startup_period_barred_by_earlier_floor_or_startup", period)
        # Reg. 63(1)(a) until 22 September 2020: only a trade begun in the
        # previous 12 months had a start-up period.
        new_trade_only = (
            p.means_test.minimum_income_floor.start_up_period.requires_new_trade
        )
        return where(
            new_trade_only,
            False,
            all_requirements
            & entered_this_year
            & found_gainfully_self_employed
            & ~barred,
        )
