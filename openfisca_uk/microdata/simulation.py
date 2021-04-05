from typing import Tuple, Union, Dict
from openfisca_core.populations import Population
import pandas as pd
import openfisca_uk
from openfisca_uk.entities import *
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_uk.microdata.frs.dataset import FRSDataset
from openfisca_uk.microdata.spi.dataset import SPIDataset
from openfisca_uk.microdata.frs.config import from_FRS
from openfisca_uk.microdata.spi.config import from_SPI
from openfisca_core.model_api import *
import numpy as np
import microdf as mdf


class Microsimulation:
    def __init__(
        self, mode: str = "frs", year: int = 2018, input_year: int = None, *reforms: Tuple[Reform]
    ):
        self.mode = mode
        self.year = year
        self.input_year = input_year or year
        self.reforms = reforms
        if mode == "frs":
            self.reforms = from_FRS, *self.reforms
            self.simulation = self.load_dataset(FRSDataset(year).entity_dfs)
            self.entity_weights = dict(
                person=self.calc("P_GROSS4", weighted=False),
                benunit=self.calc("B_GROSS4", weighted=False),
                household=self.calc("H_GROSS4", weighted=False)
            )
        elif mode == "spi":
            self.reforms = from_SPI, *self.reforms
            self.simulation = self.load_dataset(SPIDataset(year).entity_dfs)
            self.entity_weights = dict(
                person=self.calc("FACT", weighted=False),
                benunit=self.calc("FACT", weighted=False),
                household=self.calc("FACT", weighted=False)
            )

    def map_to(self, arr: np.array, entity: str, target_entity: str, how: str = None):
        entity_pop = self.simulation.populations[entity]
        target_pop = self.simulation.populations[target_entity]
        if entity == "person" and target_entity in ("benunit", "household"):
            if how and how not in ("sum", "any", "min", "max", "all", "value_from_first_person"):
                raise ValueError("Not a valid function.")
            return target_pop.__getattribute__(how or "sum")(arr)
        elif entity in ("benunit", "household") and target_entity == "person":
            if not how:
                return entity_pop.project(arr)
            if how == "mean":
                return entity_pop.project(arr / entity_pop.nb_persons())
        else:
            return self.map_to(self.map_to(arr, entity, "person", how="mean"), "person", target_entity, how="sum")

    def calc(self, var: str, period: Union[str, int] = None, weighted: bool = True, map_to: str = None, how: str = None):
        if period is None:
            period = self.input_year
        arr = self.simulation.calculate(var, period)
        if not weighted:
            return arr
        else:
            entity = self.simulation.tax_benefit_system.variables[var].entity.key
            if map_to:
                arr = self.map_to(arr, entity, map_to, how=how)
                entity = map_to
            return mdf.MicroSeries(arr, weights=self.entity_weights[entity])

    def load_dataset(
        self, entity_dfs: Tuple[pd.DataFrame], verbose: bool = False
    ) -> None:
        person, benunit, household = entity_dfs
        system = openfisca_uk.CountryTaxBenefitSystem()
        for reform in self.reforms:
            # apply each reform
            system = reform(system)
        builder = SimulationBuilder()
        builder.create_entities(system)
        person.sort_values("P_person_id", inplace=True)
        benunit.sort_values("B_benunit_id", inplace=True)
        household.sort_values("H_household_id", inplace=True)
        person["id"] = person["P_person_id"]
        benunit["id"] = benunit["B_benunit_id"]
        household["id"] = household["H_household_id"]
        person.sort_values("id", inplace=True)
        person.reset_index(inplace=True, drop=True)
        benunit.sort_values("id", inplace=True)
        benunit.reset_index(inplace=True, drop=True)
        household.sort_values("id", inplace=True)
        household.reset_index(inplace=True, drop=True)
        self.relations = {
            "person": np.array(person["P_person_id"]),
            "benunit": np.array(benunit["B_benunit_id"]),
            "household": np.array(household["H_household_id"]),
            "person-benunit": np.array(person["P_benunit_id"]),
            "person-household": np.array(person["P_household_id"]),
        }
        person_ids = np.array(person["P_person_id"])
        benunit_ids = np.array(benunit["B_benunit_id"])
        household_ids = np.array(household["H_household_id"])
        builder.declare_person_entity("person", person_ids)
        benunits = builder.declare_entity("benunit", benunit_ids)
        households = builder.declare_entity("household", household_ids)
        person_roles = np.array(person["P_role"])
        builder.join_with_persons(
            benunits, person["P_benunit_id"], person_roles
        )  # define person-benunit memberships
        builder.join_with_persons(
            households, np.array(person["P_household_id"]), person_roles
        )  # define person-household memberships
        model = builder.build(system)
        skipped = []
        for input_file in [person, benunit, household]:
            for column in input_file.columns:
                if column != "P_role":
                    try:
                        def_period = system.get_variable(
                            column
                        ).definition_period
                        if def_period in ["eternity", "year"]:
                            input_periods = [self.input_year]
                        else:
                            input_periods = period(
                                self.input_year
                            ).get_subperiods(def_period)
                        for subperiod in input_periods:
                            model.set_input(
                                column, subperiod, np.array(input_file[column])
                            )
                    except Exception:
                        skipped += [column]
        if skipped and verbose:
            print(
                f"Incomplete initialisation: skipped {len(skipped)} variables:"
            )
            for var in skipped:
                print(f"{var}")
        return model