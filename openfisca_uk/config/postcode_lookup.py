from openfisca_uk.model_api import *
from openfisca_uk.variables.demographic.locations import LocalAuthority
import pandas as pd

PC = pd.read_csv(DATA_FOLDER / "geography" / "postcodes.csv")
LA = pd.read_csv(DATA_FOLDER / "geography" / "local_authorities.csv")
LA_safe_name = (
    lambda x: x.upper()
    .replace(" ", "_")
    .replace("&", "")
    .replace("-", "_")
    .replace("__", "_")
    .replace("'", "")
    .replace(",", "")
    .replace(".", "")
)
LAC_LA = LA.set_index("LAD20CD").LAD20NM.apply(LA_safe_name).sort_values()
LAC_LA = LAC_LA[(PC.laua[PC.laua.isin(LAC_LA.index)]).unique()]
PC_LAC = PC.set_index("pcd").laua
LA_index = (
    LAC_LA.sort_values()
    .reset_index()
    .reset_index()
    .set_index("LAD20NM")["index"]
)


class postcode(Variable):
    value_type = str
    entity = Household
    label = "Postcode for the household"
    definition_period = YEAR


class local_authority(Variable):
    value_type = Enum
    possible_values = LocalAuthority
    default_value = LocalAuthority.MAIDSTONE
    entity = Household
    label = "The Local Authority for the household"
    definition_period = YEAR

    def formula(household, period, parameters):
        return LA_index[LAC_LA[PC_LAC[household("postcode", period)]]]


class with_postcode_features(Reform):
    def apply(self):
        self.add_variable(postcode)
        self.update_variable(local_authority)
