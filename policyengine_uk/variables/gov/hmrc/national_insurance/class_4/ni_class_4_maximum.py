from policyengine_uk.model_api import *


class ni_class_4_maximum(Variable):
    label = "NI Class 4 maximum liability"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2001/1004/regulation/100"

    def formula(person, period, parameters):
        ni = parameters(period).gov.hmrc.national_insurance
        upl = ni.class_4.thresholds.upper_profits_limit
        lpl = ni.class_4.thresholds.lower_profits_limit
        step_1 = upl - lpl
        main_rate = ni.class_4.rates.main
        add_rate = ni.class_4.rates.additional
        step_2 = step_1 * main_rate
        # Class 2 contributions drop out of regulation 100 from 6 April 2024.
        includes_class_2 = ni.class_4.annual_maximum.includes_class_2
        class_2_weeks_addition = 53 * ni.class_2.flat_rate * includes_class_2
        step_3 = step_2 + class_2_weeks_addition
        class_2_contributions = person("ni_class_2", period) * includes_class_2
        primary_class_1_contributions = person("ni_class_1_employee_primary", period)
        step_4_raw = step_3 - class_2_contributions - primary_class_1_contributions
        step_4 = max_(step_4_raw, 0)
        # Case 1: Step Four exceeds primary Class 1 + Class 2 + main-rate
        # Class 4. Main-rate Class 4 is Step Two less the main rate on the
        # unused part of the main band, so this is equivalent to
        #   main rate x unused band + 53 weekly Class 2 rates
        #     > 2 x (primary Class 1 + Class 2).
        # Comparing the totals directly left the case to float32 rounding
        # when they were equal (profits above the UPL, no Class 1 or 2), and
        # a wrong Case 1 dropped the additional-rate band (#1878). The unused
        # band is exactly zero at or above the UPL, so that equality is now
        # decided exactly.
        profits = person("self_employment_income", period)
        unused_main_band = clip(upl - profits.astype(np.float64), 0, step_1)
        case_1 = (step_4_raw >= 0) & (
            main_rate * unused_main_band + class_2_weeks_addition
            > 2
            * (
                class_2_contributions.astype(np.float64)
                + primary_class_1_contributions.astype(np.float64)
            )
        )
        # Step Five converts Step Four back to profits at the main rate. With a
        # zero main rate (a reform abolishing it) there is no main-rate
        # liability to limit, so the headroom is unlimited instead of 0 / 0.
        step_5 = np.divide(
            step_4,
            main_rate,
            out=np.full_like(step_4, np.inf),
            where=main_rate > 0,
        )
        step_6 = min_(upl, profits) - lpl
        step_7 = max_(0, step_6 - step_5)
        step_8 = step_7 * add_rate
        step_9 = max_(0, profits - upl) * add_rate

        return where(case_1, step_4, step_4 + step_8 + step_9)
