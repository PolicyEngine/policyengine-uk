from policyengine_uk.model_api import *

label = "Region"


class Region(Enum):
    UNKNOWN = "Unknown"
    NORTH_EAST = "North East"
    NORTH_WEST = "North West"
    YORKSHIRE = "Yorkshire and the Humber"
    EAST_MIDLANDS = "East Midlands"
    WEST_MIDLANDS = "West Midlands"
    EAST_OF_ENGLAND = "East of England"
    LONDON = "London"
    SOUTH_EAST = "South East"
    SOUTH_WEST = "South West"
    WALES = "Wales"
    SCOTLAND = "Scotland"
    NORTHERN_IRELAND = "Northern Ireland"
