from openfisca_uk.variables.demographic.household import TenureType
from openfisca_uk.variables.finance.income import EmploymentStatus
from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *
from openfisca_uk.microdata.frs.frs_variables import FRS_variables

class tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = Household
    label = u'Tenure type of the household'
    definition_period = YEAR

    def formula(household, period, parameters):
        value = household("H_PTENTYP2", period)
        result = select(
            [
                value == 1,
                value == 2,
                (value == 3) + (value == 4),
                value == 5,
                value == 6
            ],
            [
                TenureType.RENT_FROM_COUNCIL,
                TenureType.RENT_FROM_HA,
                TenureType.RENT_PRIVATELY,
                TenureType.OWNED_OUTRIGHT,
                TenureType.OWNED_WITH_MORTGAGE
            ]
        )
        return result


class employment_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from employment'
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("P_UGRSPAY", period) * WEEKS_IN_YEAR

class employment_expenses(Variable):
    value_type = float
    entity = Person
    label = u'Cost of expenses necessarily incurred and reimbursed by employment'
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 333"

    def formula(person, period, parameters):
        EXPENSES = [
            "P_FUELAMT",
            "P_MILEAMT",
            "P_MOTAMT"
        ]
        return add(person, period, EXPENSES)

class pension_contributions(Variable):
    value_type = float
    entity = Person
    label = u'Amount contributed to registered pension schemes paid by the individual (not the employer)'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_UDEDUC1", period) * WEEKS_IN_YEAR

class pension_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from pensions'
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"

    def formula(person, period, parameters):
        return person("P_INPENINC", period) * WEEKS_IN_YEAR

class trading_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from trading profits'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("P_SEINCAMT", period) * WEEKS_IN_YEAR

class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from interest on savings'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"

    def formula(person, period, parameters):
        SAVINGS_ACCOUNT_CODES = [
            1,
            2,
            3,
            4,
            5,
            6,
            10,
            11,
            12,
            14,
            16,
            17,
            18,
            19,
            21,
            25,
            26,
            27,
            28,
            29,
            30
        ]
        savings_accounts = [f"P_ACCINT_ACCOUNT_CODE_{i}" for i in SAVINGS_ACCOUNT_CODES]
        return add(person, period, savings_accounts) * WEEKS_IN_YEAR

class tax_free_savings_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from savings in tax-free accounts'
    definition_period = YEAR

    def formula(person, period, parameters):
        TAX_FREE_SAVINGS_ACCOUNT_CODES = [
            6,
            14,
            21,
        ]
        accounts = [f"P_ACCINT_ACCOUNT_CODE_{i}" for i in TAX_FREE_SAVINGS_ACCOUNT_CODES]
        return add(person, period, accounts) * WEEKS_IN_YEAR

class dividend_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from dividends'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"

    def formula(person, period, parameters):
        DIVIDEND_ACCOUNT_CODES = [
            7,
            8,
            9,
            13,
            22,
            23,
            24
        ]
        dividend_accounts = [f"P_ACCINT_ACCOUNT_CODE_{i}" for i in DIVIDEND_ACCOUNT_CODES]
        return add(person, period, dividend_accounts) * WEEKS_IN_YEAR

class sublet_income(Variable):
    value_type = float
    entity = Person
    label = u'Income received from sublet agreements'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("H_SUBLET", period) * WEEKS_IN_YEAR

class tax_reported(Variable):
    value_type = float
    entity = Person
    label = u'Reported tax paid'
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("P_INDINC", period) - person("P_NINDINC", period)) * WEEKS_IN_YEAR

class base_net_income(Variable):
    value_type = float
    entity = Person
    label = u'Existing net income for the person to use as a base in microsimulation'
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("P_NINDINC", period) + person("P_CHINCDV", period)) * WEEKS_IN_YEAR

class person_weight(Variable):
    value_type = float
    entity = Person
    label = u'Weight factor for the person'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.household("H_GROSS4", period)

class benunit_weight(Variable):
    value_type = float
    entity = BenUnit
    label = u'Weight factor for the benefit unit'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("B_GROSS4", period)

class household_weight(Variable):
    value_type = float
    entity = Household
    label = u'Weight factor for the household'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("H_GROSS4", period)

class AA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Attendance Allowance (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_12", period.this_year)

class BSP_reported(Variable):
    value_type = float
    entity = Person
    label = u"Bereavement Support Payment (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_6", period.this_year)

class carers_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Carer's Allowance (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_13", period.this_year)

class DLA_M_reported(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (mobility component) (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_2", period.this_year)

class DLA_SC_reported(Variable):
    value_type = float
    entity = Person
    label = u"Disability Living Allowance (self-care) (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_1", period.this_year)

class ESA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Employment and Support Allowance (contribution-based) (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_16", period.this_year)

class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"ESA (income-based) (reported amount per week)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_1016", period.this_year)

class IIDB_reported(Variable):
    value_type = float
    entity = Person
    label = u"Industrial Injuries Disablement Benefit (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_15", period.this_year)

class incapacity_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Incapacity Benefit (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_17", period.this_year)

class JSA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Job Seeker's Allowance (contribution-based) (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_14", period.this_year)

class PIP_DL_reported(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Daily Living) (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_96", period.this_year)

class PIP_M_reported(Variable):
    value_type = float
    entity = Person
    label = u"Personal Independence Payment (Mobility) (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_97", period.this_year)


class SDA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Severe Disablement Allowance (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_10", period.this_year)

class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = u'Reported income from the State Pension'
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_5", period.this_year)

class child_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Child Benefit (reported amount)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_3", period.this_year)

class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"ESA (income-based) (reported amount per week)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_16", period.this_year)

class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Housing Benefit (reported amount per week)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_94", period.this_year)

class income_support_reported(Variable):
    value_type = float
    entity = Person
    label = u"Income Support (reported amount per week)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_19", period.this_year)

class JSA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"JSA (income-based) (reported amount per week)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_1014", period.this_year)

class pension_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Pension Credit per week"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_4", period.this_year)

class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit (reported amount)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_90", period.this_year)


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit (reported amount)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_91", period.this_year)

class universal_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Universal Credit per month"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_95", period.this_year)

class AFCS_reported(Variable):
    value_type = float
    entity = Person
    label = u"Armed Forces Compensation Scheme (reported)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_8", period.this_year)

class age(Variable):
    value_type = float
    entity = Person
    label = u'The age of the person in years'
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("P_AGE80", period) + person("P_AGE", period)

class is_household_head(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is the head-of-household'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_PERSON", period) == 1

class is_benunit_head(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is the head-of-family'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_UPERSON", period) == 1

class in_FE(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is in Further Education'
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("P_TYPEED2", period) == 7

class hours_worked(Variable):
    value_type = float
    entity = Person
    label = u'Total amount of hours worked by this person'
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("P_TOTHOURS", period)

class employment_status(Variable):
    value_type = Enum
    entity = Person
    possible_values = EmploymentStatus
    default_value = EmploymentStatus.UNEMPLOYED
    label = u'Employment status of the person'
    definition_period = YEAR

    def formula(person, period, parameters):
        value = person("P_EMPSTATI", period)
        status = select([
            value == 0, 
            value == 1, 
            value == 2, 
            value == 3, 
            value == 4, 
            value == 5,
            value == 6,
            value == 7,
            value == 8,
            value == 9,
            value == 10,
            value == 11
        ], [
            EmploymentStatus.CHILD,
            EmploymentStatus.FT_EMPLOYED,
            EmploymentStatus.PT_EMPLOYED,
            EmploymentStatus.FT_SELF_EMPLOYED,
            EmploymentStatus.PT_SELF_EMPLOYED,
            EmploymentStatus.UNEMPLOYED,
            EmploymentStatus.RETIRED,
            EmploymentStatus.STUDENT,
            EmploymentStatus.CARER,
            EmploymentStatus.LONG_TERM_DISABLED,
            EmploymentStatus.SHORT_TERM_DISABLED,
            EmploymentStatus.OTHER_INACTIVE
        ])
        return status

input_variables = [
    tenure_type,
    employment_income,
    pension_contributions,
    pension_income,
    trading_income,
    savings_interest_income,
    dividend_income,
    tax_free_savings_income,
    sublet_income,
    tax_reported,
    base_net_income,
    person_weight,
    benunit_weight,
    household_weight,
    AA_reported,
    BSP_reported,
    carers_allowance_reported,
    DLA_M_reported,
    DLA_SC_reported,
    ESA_contrib_reported,
    IIDB_reported,
    incapacity_benefit_reported,
    JSA_contrib_reported,
    PIP_DL_reported,
    PIP_M_reported,
    SDA_reported,
    state_pension_reported,
    child_benefit_reported,
    ESA_income_reported,
    housing_benefit_reported,
    income_support_reported,
    JSA_income_reported,
    pension_credit_reported,
    working_tax_credit_reported,
    child_tax_credit_reported,
    universal_credit_reported,
    AFCS_reported,
    age,
    is_benunit_head,
    is_household_head,
    in_FE,
    hours_worked,
    employment_status,
    employment_expenses
]


class from_FRS(Reform):
    def apply(self):
        for var in FRS_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)
