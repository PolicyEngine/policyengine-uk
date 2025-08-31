from policyengine_uk.model_api import *

label = "Firm"
description = "Business firm variables from firm dataset."


class firm_id(Variable):
    value_type = int
    entity = Firm
    label = "firm ID"
    documentation = "Unique identifier for each firm"
    definition_period = YEAR
    quantity_type = STOCK


class firm_sector_id(Variable):
    value_type = int
    entity = Firm
    label = "firm sector ID"
    documentation = "Identifier linking firm to its sector"
    definition_period = YEAR
    quantity_type = STOCK


class firm_business_group_id(Variable):
    value_type = int
    entity = Firm
    label = "firm business group ID"
    documentation = "Identifier linking firm to its business group"
    definition_period = YEAR
    quantity_type = STOCK


class year(Variable):
    value_type = int
    entity = Firm
    label = "year"
    documentation = "Year of the data"
    definition_period = YEAR
    quantity_type = STOCK


class firm_weight(Variable):
    value_type = float
    entity = Firm
    label = "firm weight"
    documentation = "Statistical weight for firm in population"
    definition_period = YEAR
    quantity_type = STOCK


class sic_code(Variable):
    value_type = str
    entity = Firm
    label = "SIC code"
    documentation = "Standard Industrial Classification code"
    definition_period = YEAR
    quantity_type = STOCK


class annual_turnover_k(Variable):
    value_type = float
    entity = Firm
    label = "annual turnover (thousands)"
    documentation = "Annual turnover in thousands of pounds"
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW


class annual_input_k(Variable):
    value_type = float
    entity = Firm
    label = "annual input (thousands)"
    documentation = "Annual input costs in thousands of pounds"
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW


class vat_liability_k(Variable):
    value_type = float
    entity = Firm
    label = "VAT liability (thousands)"
    documentation = "VAT liability in thousands of pounds"
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW


class employment(Variable):
    value_type = int
    entity = Firm
    label = "employment"
    documentation = "Number of employees"
    definition_period = YEAR
    quantity_type = STOCK


class vat_registered(Variable):
    value_type = bool
    entity = Firm
    label = "VAT registered"
    documentation = "Whether the firm is registered for VAT"
    definition_period = YEAR
    quantity_type = STOCK


class hmrc_band(Variable):
    value_type = str
    entity = Firm
    label = "HMRC band"
    documentation = "HMRC size band classification"
    definition_period = YEAR
    quantity_type = STOCK


class employment_band(Variable):
    value_type = str
    entity = Firm
    label = "employment band"
    documentation = "Employment size band classification"
    definition_period = YEAR
    quantity_type = STOCK


class sic_numeric(Variable):
    value_type = int
    entity = Firm
    label = "SIC numeric"
    documentation = "Numeric version of SIC code"
    definition_period = YEAR
    quantity_type = STOCK
