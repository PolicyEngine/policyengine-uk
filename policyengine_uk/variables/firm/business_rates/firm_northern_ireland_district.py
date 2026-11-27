from policyengine_uk.model_api import *


class NorthernIrelandDistrict(Enum):
    UNKNOWN = "Unknown"
    ANTRIM_AND_NEWTOWNABBEY = "Antrim and Newtownabbey"
    ARDS_AND_NORTH_DOWN = "Ards and North Down"
    ARMAGH_CITY_BANBRIDGE_AND_CRAIGAVON = "Armagh City, Banbridge and Craigavon"
    BELFAST = "Belfast"
    CAUSEWAY_COAST_AND_GLENS = "Causeway Coast and Glens"
    DERRY_CITY_AND_STRABANE = "Derry City and Strabane"
    FERMANAGH_AND_OMAGH = "Fermanagh and Omagh"
    LISBURN_AND_CASTLEREAGH = "Lisburn and Castlereagh"
    MID_AND_EAST_ANTRIM = "Mid and East Antrim"
    MID_ULSTER = "Mid Ulster"
    NEWRY_MOURNE_AND_DOWN = "Newry, Mourne and Down"


class firm_northern_ireland_district(Variable):
    value_type = Enum
    entity = Firm
    label = "Firm Northern Ireland district council"
    documentation = (
        "The district council area of the firm's property, for a firm whose "
        "firm_region is Northern Ireland. Its district rate is added to the "
        "regional rate. At the default, UNKNOWN, a Northern Ireland firm's "
        "business rates are not modelled and are 0. Ignored outside "
        "Northern Ireland."
    )
    definition_period = YEAR
    hidden_input = True
    possible_values = NorthernIrelandDistrict
    default_value = NorthernIrelandDistrict.UNKNOWN
    reference = "https://www.legislation.gov.uk/nisi/1977/2157/article/6"
