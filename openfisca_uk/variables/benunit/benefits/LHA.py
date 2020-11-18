from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class LHA_eligible(Variable):
    value_type = float
    entity = BenUnit
    label = u'Whether eligible for Housing Benefit'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.max(not_(benunit.members("living_in_social_housing", period)) * benunit.members("is_renting", period))

class LHA_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u'Applicable amount for LHA'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        rates = parameters(period).benefits.LHA.rate_caps
        rent = benunit.sum(benunit.members("personal_rent", period))
        num_rooms = benunit.max(benunit.members("num_rooms_in_household", period))
        is_shared = benunit.max(benunit.members("living_in_shared_accomodation", period)) > 0
        rate_cap = select([is_shared, num_rooms == 1, num_rooms == 2, num_rooms == 3, num_rooms > 3], [rates.shared, rates.beds_1, rates.beds_2, rates.beds_3, rates.beds_4])
        amount = min_(rent, rate_cap)
        return amount

class LHA_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u'Relevant income for Housing Benefit'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        means_test = parameters(period).benefits.LHA.means_test
        BENUNIT_MEANS_TESTED_BENEFITS = ["working_tax_credit"]
        PERSON_MEANS_TESTED_BENEFITS = ["JSA_contrib"]
        benefits = aggr(benunit, period, PERSON_MEANS_TESTED_BENEFITS) + add(
            benunit, period, BENUNIT_MEANS_TESTED_BENEFITS
        )
        means_tested_income = (
            benunit("benunit_post_tax_income", period, options=[MATCH])
            + benefits
        )
        applicable_income = max_(
            0,
            means_tested_income
            - benunit("is_single_person", period)
            * means_test.income_disregard_single
            - benunit("is_couple", period)
            * means_test.income_disregard_couple
            - benunit("is_lone_parent", period)
            * means_test.income_disregard_lone_parent
            - (benunit("benunit_hours", period.this_year) > means_test.worker_hours)
            * means_test.worker_income_disregard,
        )
        return applicable_income

class LHA(Variable):
    value_type = float
    entity = BenUnit
    label = u'Local Housing Allowance'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        rent = benunit.sum(benunit.members("personal_rent", period))
        amount = benunit("LHA_applicable_amount", period)
        income = benunit("LHA_applicable_income", period)
        withdrawal_rate = parameters(period).benefits.LHA.means_test.withdrawal_rate
        final_amount = rent - max_(0, income - amount) * withdrawal_rate
        return final_amount