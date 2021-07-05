from openfisca_uk.variables.demographic.person import Gender
from openfisca_uk.variables.demographic.household import (
    AccommodationType,
    Region,
    TenureType,
)
from openfisca_uk.variables.finance.income import EmploymentStatus
from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *
from openfisca_uk.microdata.frs.frs_variables import FRS_variables


class self_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Income from self-employmen. Different to trading profits"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_SEINCAM2", period) * WEEKS_IN_YEAR


class property_income(Variable):
    value_type = float
    entity = Person
    label = "Income from rental of property"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(b)"

    def formula(person, period, parameters):
        return (
            person("sublet_income", period)
            + person("P_ROYYR1", period) * WEEKS_IN_YEAR
        )


class gender(Variable):
    value_type = Enum
    possible_values = Gender
    default_value = Gender.MALE
    entity = Person
    label = "Gender of the person"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return where(person("P_SEX", period) == 1, Gender.MALE, Gender.FEMALE)


class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "Income from other sources"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_INRINC", period) * WEEKS_IN_YEAR - person(
            "property_income", period
        )


class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.UNKNOWN
    entity = Household
    label = "Region of the UK"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        region = household("H_GVTREGNO", period)
        reg = select(
            [
                region == 1,
                region == 2,
                region == 4,
                region == 5,
                region == 6,
                region == 7,
                region == 8,
                region == 9,
                region == 10,
                region == 11,
                region == 12,
                region == 13,
            ],
            [
                Region.NORTH_EAST,
                Region.NORTH_WEST,
                Region.YORKSHIRE,
                Region.EAST_MIDLANDS,
                Region.WEST_MIDLANDS,
                Region.EAST_OF_ENGLAND,
                Region.LONDON,
                Region.SOUTH_EAST,
                Region.SOUTH_WEST,
                Region.SCOTLAND,
                Region.WALES,
                Region.NORTHERN_IRELAND,
            ],
        )
        return reg


class tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = Household
    label = "Tenure type of the household"
    definition_period = YEAR

    def formula(household, period, parameters):
        value = household("H_PTENTYP2", period)
        result = select(
            [
                value == 1,
                value == 2,
                (value == 3) + (value == 4),
                value == 5,
                value == 6,
            ],
            [
                TenureType.RENT_FROM_COUNCIL,
                TenureType.RENT_FROM_HA,
                TenureType.RENT_PRIVATELY,
                TenureType.OWNED_OUTRIGHT,
                TenureType.OWNED_WITH_MORTGAGE,
            ],
        )
        return result


class rent(Variable):
    value_type = float
    entity = Household
    label = "Gross rent for the household"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("H_HHRENT", period) * WEEKS_IN_YEAR


class employment_income(Variable):
    value_type = float
    entity = Person
    label = "Income from employment"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("P_UGRSPAY", period) * WEEKS_IN_YEAR


class employment_expenses(Variable):
    value_type = float
    entity = Person
    label = (
        "Cost of expenses necessarily incurred and reimbursed by employment"
    )
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 333"

    def formula(person, period, parameters):
        EXPENSES = ["P_FUELAMT", "P_MILEAMT", "P_MOTAMT"]
        return add(person, period, EXPENSES)


class pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Amount contributed to registered pension schemes paid by the individual (not the employer)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_UDEDUC1", period) * WEEKS_IN_YEAR


class pension_income(Variable):
    value_type = float
    entity = Person
    label = "Income from pensions"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"

    def formula(person, period, parameters):
        return person("P_INPENINC", period) * WEEKS_IN_YEAR


class trading_income(Variable):
    value_type = float
    entity = Person
    label = "Income from trading profits"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("P_SEINCAMT", period) * WEEKS_IN_YEAR


class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Income from interest on savings"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"

    def formula(person, period, parameters):
        return person("P_ININV", period) * WEEKS_IN_YEAR - person(
            "dividend_income", period
        )


class tax_free_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Income from savings in tax-free accounts"
    definition_period = YEAR

    def formula(person, period, parameters):
        TAX_FREE_SAVINGS_ACCOUNT_CODES = [
            6,
            14,
            21,
        ]
        accounts = [
            f"P_ACCINT_ACCOUNT_CODE_{i}"
            for i in TAX_FREE_SAVINGS_ACCOUNT_CODES
        ]
        return add(person, period, accounts) * WEEKS_IN_YEAR


class dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Income from dividends"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"

    def formula(person, period, parameters):
        DIVIDEND_ACCOUNT_CODES = [7, 8, 9, 13, 22, 23, 24]
        dividend_accounts = [
            f"P_ACCINT_ACCOUNT_CODE_{i}" for i in DIVIDEND_ACCOUNT_CODES
        ]
        return add(person, period, dividend_accounts) * WEEKS_IN_YEAR


class sublet_income(Variable):
    value_type = float
    entity = Person
    label = "Income received from sublet agreements"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("H_SUBLET", period) * WEEKS_IN_YEAR


class tax_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported tax paid"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            person("P_INDINC", period) - person("P_NINDINC", period)
        ) * WEEKS_IN_YEAR


class base_net_income(Variable):
    value_type = float
    entity = Person
    label = "Existing net income for the person to use as a base in microsimulation"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            person("P_NINDINC", period) + person("P_CHINCDV", period)
        ) * WEEKS_IN_YEAR


class person_weight(Variable):
    value_type = float
    entity = Person
    label = "Weight factor for the person"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.household("H_GROSS4", period)


class benunit_weight(Variable):
    value_type = float
    entity = BenUnit
    label = "Weight factor for the benefit unit"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("B_GROSS4", period)


class household_weight(Variable):
    value_type = float
    entity = Household
    label = "Weight factor for the household"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("H_GROSS4", period)


class AA_reported(Variable):
    value_type = float
    entity = Person
    label = "Attendance Allowance (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_12", period) * WEEKS_IN_YEAR


class BSP_reported(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_6", period) * WEEKS_IN_YEAR


class carers_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_13", period) * WEEKS_IN_YEAR


class DLA_M_reported(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance (mobility component) (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_2", period) * WEEKS_IN_YEAR


class DLA_SC_reported(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance (self-care) (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_1", period) * WEEKS_IN_YEAR


class ESA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = "Employment and Support Allowance (contribution-based) (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_16", period) * WEEKS_IN_YEAR


class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = "ESA (income-based) (reported amount per week)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_1016", period) * WEEKS_IN_YEAR


class IIDB_reported(Variable):
    value_type = float
    entity = Person
    label = "Industrial Injuries Disablement Benefit (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_15", period) * WEEKS_IN_YEAR


class incapacity_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Incapacity Benefit (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_17", period) * WEEKS_IN_YEAR


class JSA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = "Job Seeker's Allowance (contribution-based) (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_14", period) * WEEKS_IN_YEAR


class PIP_DL_reported(Variable):
    value_type = float
    entity = Person
    label = "Personal Independence Payment (Daily Living) (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_96", period) * WEEKS_IN_YEAR


class PIP_M_reported(Variable):
    value_type = float
    entity = Person
    label = "Personal Independence Payment (Mobility) (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_97", period) * WEEKS_IN_YEAR


class SDA_reported(Variable):
    value_type = float
    entity = Person
    label = "Severe Disablement Allowance (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_10", period) * WEEKS_IN_YEAR


class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported income from the State Pension"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_5", period) * WEEKS_IN_YEAR


class child_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Child Benefit (reported amount)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_3", period) * WEEKS_IN_YEAR


class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = "ESA (income-based) (reported amount)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_16", period) * WEEKS_IN_YEAR


class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit (reported amount)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_94", period) * WEEKS_IN_YEAR


class income_support_reported(Variable):
    value_type = float
    entity = Person
    label = "Income Support (reported amount)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_19", period) * WEEKS_IN_YEAR


class JSA_income_reported(Variable):
    value_type = float
    entity = Person
    label = "JSA (income-based) (reported amount)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_1014", period) * WEEKS_IN_YEAR


class pension_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported amount of Pension Credit per week"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_4", period) * WEEKS_IN_YEAR


class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Working Tax Credit (reported amount)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_90", period) * WEEKS_IN_YEAR


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Working Tax Credit (reported amount)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_91", period) * WEEKS_IN_YEAR


class universal_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported amount of Universal Credit"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_INDUC", period) * WEEKS_IN_YEAR


class benefits_reported(Variable):
    value_type = float
    entity = Person
    label = "Total simulated"
    definition_period = YEAR

    def formula(person, period, parameters):
        FRS_BENEFITS = [
            "P_INOTHBEN",
            "P_INRPINC",
            "P_INDISBEN",
            "P_INTXCRED",
            "P_INDUC",
        ]
        total_benefits = add(person, period, FRS_BENEFITS) * WEEKS_IN_YEAR
        return total_benefits


class AFCS_reported(Variable):
    value_type = float
    entity = Person
    label = "Armed Forces Compensation Scheme (reported)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_BENAMT_BENEFIT_CODE_8", period) * WEEKS_IN_YEAR


class age(Variable):
    value_type = float
    entity = Person
    label = "The age of the person in years"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("P_AGE80", period) + person("P_AGE", period)


class is_household_head(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the head-of-household"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_PERSON", period) == 1


class is_benunit_head(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the head-of-family"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_UPERSON", period) == 1


class in_FE(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is in Further Education"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("P_TYPEED2", period) == 7


class hours_worked(Variable):
    value_type = float
    entity = Person
    label = "Total amount of hours worked by this person"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_TOTHOURS", period) * WEEKS_IN_YEAR


class employment_status(Variable):
    value_type = Enum
    entity = Person
    possible_values = EmploymentStatus
    default_value = EmploymentStatus.UNEMPLOYED
    label = "Employment status of the person"
    definition_period = YEAR

    def formula(person, period, parameters):
        value = person("P_EMPSTATI", period)
        status = select(
            [
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
                value == 11,
            ],
            [
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
                EmploymentStatus.OTHER_INACTIVE,
            ],
        )
        return status


class housing_costs(Variable):
    value_type = float
    entity = Household
    label = "Total housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return (
            household("H_GBHSCOST", period)
            + household("H_NIHSCOST", period) * WEEKS_IN_YEAR
        )


class council_tax(Variable):
    value_type = float
    entity = Household
    label = "Council Tax"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("H_CTANNUAL", period)


class person_id(Variable):
    value_type = float
    entity = Person
    label = "ID for the person"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_person_id", period)


class benunit_id(Variable):
    value_type = float
    entity = BenUnit
    label = "ID for the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("B_benunit_id", period)


class household_id(Variable):
    value_type = float
    entity = Household
    label = "ID for the household"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("H_household_id", period)


class accommodation_type(Variable):
    value_type = Enum
    possible_values = AccommodationType
    default_value = AccommodationType.UNKNOWN
    entity = Household
    label = "Type of accommodation"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        a = household("H_TYPEACC", period)
        return select(
            [
                a == 1,
                a == 2,
                a == 3,
                a == 4,
                a == 5,
                a == 6,
                a == 7,
            ],
            [
                AccommodationType.HOUSE_DETACHED,
                AccommodationType.HOUSE_SEMI_DETACHED,
                AccommodationType.HOUSE_TERRACED,
                AccommodationType.FLAT,
                AccommodationType.CONVERTED_HOUSE,
                AccommodationType.MOBILE,
                AccommodationType.OTHER,
            ],
        )


class num_bedrooms(Variable):
    value_type = int
    entity = Household
    label = "The number of bedrooms in the house"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("H_BEDROOM6", period)


input_variables = [
    num_bedrooms,
    accommodation_type,
    region,
    person_id,
    benunit_id,
    household_id,
    council_tax,
    housing_costs,
    rent,
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
    employment_expenses,
    self_employment_income,
    miscellaneous_income,
    property_income,
    benefits_reported,
    gender,
]


class from_FRS(Reform):
    def apply(self):
        for var in FRS_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)
