from openfisca_uk.tools.general import *
from openfisca_uk.entities import *
from openfisca_uk.variables.demographic.household import Region
from openfisca_uk.variables.demographic.locations import (
    BRMAName,
    LocalAuthority,
)
import pandas as pd

DATA_FOLDER = Path(__file__).parent.parent / "data"

postcode_to_la_name = (
    pd.read_csv(
        DATA_FOLDER / "geography" / "postcode_to_la_name.csv.gz",
        compression="gzip",
    )
    .set_index("postcode")
    .local_authority
)
postcode_to_la_name["UNKNOWN"] = "UNKNOWN"
postcode_sector_to_brma_name = pd.read_csv(
    DATA_FOLDER / "geography" / "postcode_sector_to_brma_name.csv.gz",
    compression="gzip",
).set_index("postcode_sector")
la_name_to_region = pd.read_csv(
    DATA_FOLDER / "geography" / "la_name_to_region.csv.gz", compression="gzip"
).set_index("local_authority")

# Some postcode sectors have multiple BRMA names. We use the first one in the dataset.
postcode_sector_to_brma_name = postcode_sector_to_brma_name.groupby(
    postcode_sector_to_brma_name.index
).first()
postcode_sector_to_brma_name.loc["UNKNOWN"] = "UNKNOWN"


def postcode_to_postcode_sector(array):
    return pd.Series(array).apply(
        lambda postcode: postcode.replace(" ", "")[:-2]
    )


class postcode(Variable):
    value_type = str
    entity = Household
    label = u"Postcode for the household"
    definition_period = YEAR
    default_value = "UNKNOWN"


class local_authority(Variable):
    value_type = Enum
    possible_values = LocalAuthority
    default_value = LocalAuthority.MAIDSTONE
    entity = Household
    label = u"Local Authority"
    documentation = "The Local Authority for the household"
    definition_period = YEAR

    def formula(household, period, parameters):
        postcodes = (
            pd.Series(household("postcode", period))
            .str.replace(" ", "")
            .values
        )
        return postcode_to_la_name[postcodes].values.astype(str)


class postcode_sector(Variable):
    value_type = str
    entity = Household
    label = u"Postcode sector"
    definition_period = YEAR

    def formula(household, period, parameters):
        hh_postcode = household("postcode", period)
        return where(
            hh_postcode == "UNKNOWN",
            "UNKNOWN",
            postcode_to_postcode_sector(household("postcode", period)),
        )


class BRMA(Variable):
    value_type = Enum
    possible_values = BRMAName
    default_value = BRMAName.MAIDSTONE
    entity = Household
    label = u"Broad Rental Market Area"
    definition_period = YEAR

    def formula(household, period, parameters):
        return (
            postcode_sector_to_brma_name.loc[
                household("postcode_sector", period)
            ]
            .values.astype(str)
            .flatten()
        )


class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.UNKNOWN
    entity = Household
    label = u"Region"
    documentation = "Area of the UK"
    definition_period = ETERNITY
    metadata = dict(
        policyengine=dict(
            type="category",
        )
    )

    def formula(household, period, parameters):
        return (
            la_name_to_region.loc[
                household("local_authority", period).decode_to_str()
            ]
            .values.astype(str)
            .flatten()
        )


class with_postcode_features(Reform):
    def apply(self):
        self.add_variable(postcode)
        self.add_variable(postcode_sector)
        self.update_variable(BRMA)
        self.update_variable(local_authority)
        self.update_variable(region)
