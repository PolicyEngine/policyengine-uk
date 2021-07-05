import functools
from typing import List, Tuple, Union, Dict
from microdf.generic import MicroDataFrame, MicroSeries
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
from tqdm import trange

np.random.seed(0)


class Microsimulation:
    def __init__(
        self,
        *reforms: Tuple[Reform],
        mode: str = "frs",
        year: int = 2018,
        input_year: int = None,
        entity_dataframes=None,
    ):
        self.mode = mode
        self.year = year
        self.input_year = input_year or (
            year + 1
        )  # the model takes yearly parameters from the start of the year; most surveys cover a financial year and therefore it's more accurate to start with the parameters from halfway through
        self.reforms = reforms
        if mode == "frs":
            self.reforms = from_FRS, *self.reforms
            if entity_dataframes is not None:
                self.entity_dataframes = entity_dataframes
            else:
                self.entity_dataframes = FRSDataset(year).entity_dfs
            self.simulation = self.load_dataset(self.entity_dataframes)
        elif mode == "spi":
            self.reforms = from_SPI, *self.reforms
            if entity_dataframes is not None:
                self.entity_dataframes = entity_dataframes
            else:
                self.entity_dataframes = SPIDataset(year).entity_dfs
            self.simulation = self.load_dataset(self.entity_dataframes)
        self.entity_weights = dict(
            person=self.calc("person_weight", weighted=False),
            benunit=self.calc("benunit_weight", weighted=False),
            household=self.calc("household_weight", weighted=False),
        )
        self.bonus_sims = {}

    def map_to(
        self, arr: np.array, entity: str, target_entity: str, how: str = None
    ):
        entity_pop = self.simulation.populations[entity]
        target_pop = self.simulation.populations[target_entity]
        if entity == "person" and target_entity in ("benunit", "household"):
            if how and how not in (
                "sum",
                "any",
                "min",
                "max",
                "all",
                "value_from_first_person",
            ):
                raise ValueError("Not a valid function.")
            return target_pop.__getattribute__(how or "sum")(arr)
        elif entity in ("benunit", "household") and target_entity == "person":
            if not how:
                return entity_pop.project(arr)
            if how == "mean":
                return entity_pop.project(arr / entity_pop.nb_persons())
        elif entity == target_entity:
            return arr
        else:
            return self.map_to(
                self.map_to(arr, entity, "person", how="mean"),
                "person",
                target_entity,
                how="sum",
            )

    def calc(
        self,
        var: str,
        period: Union[str, int] = None,
        weighted: bool = True,
        map_to: str = None,
        how: str = None,
        dp: int = 2,
    ) -> MicroSeries:
        if period is None:
            period = self.input_year
        try:
            var_metadata = self.simulation.tax_benefit_system.variables[var]
            arr = self.simulation.calculate(var, period)
        except Exception as e:
            try:
                arr = self.simulation.calculate_add(var, period)
                if var_metadata.value_type == bool:
                    arr = arr >= 52
            except:
                try:
                    arr = self.simulation.calculate_divide(var, period)
                except:
                    raise e
        if var_metadata.value_type == float:
            arr = arr.round(2)
        if var_metadata.value_type == Enum:
            arr = arr.decode_to_str()
        if not weighted:
            return arr
        else:
            entity = var_metadata.entity.key
            if map_to:
                arr = self.map_to(arr, entity, map_to, how=how)
                entity = map_to
            return mdf.MicroSeries(arr, weights=self.entity_weights[entity])

    def df(
        self, vars: List[str], period: Union[str, int] = None, map_to=None
    ) -> MicroDataFrame:
        df = pd.DataFrame()
        entity = (
            map_to
            or self.simulation.tax_benefit_system.variables[vars[0]].entity.key
        )
        for var in vars:
            df[var] = self.calc(var, period=period, map_to=entity)
        df = MicroDataFrame(df, weights=self.entity_weights[entity])
        return df

    def apply_reforms(self, reforms: list) -> None:
        """Applies a list of reforms to the tax-benefit system.

        Args:
            reforms (list): A list of reforms. Each reform can also be a list of reforms.
        """
        for reform in reforms:
            if isinstance(reform, tuple) or isinstance(reform, list):
                self.apply_reforms(reform)
            else:
                self.system = reform(self.system)

    def load_dataset(
        self, entity_dfs: Tuple[pd.DataFrame], verbose: bool = False
    ) -> None:
        person, benunit, household = entity_dfs
        self.system = openfisca_uk.CountryTaxBenefitSystem()
        self.apply_reforms(self.reforms)
        builder = SimulationBuilder()
        builder.create_entities(self.system)
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
        model = builder.build(self.system)
        skipped = []
        for input_file in [person, benunit, household]:
            for column in input_file.columns:
                if column != "P_role":
                    try:
                        def_period = self.system.get_variable(
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

    def deriv(
        self,
        target="tax",
        wrt="employment_income",
        delta=100,
        percent=False,
        group_limit=2,
    ) -> MicroSeries:
        """Calculates effective marginal tax rates over a population.

        Args:
            targets (str, optional): The name of the variable to measure the derivative of. Defaults to "household_net_income".
            wrt (str, optional): The name of the independent variable. Defaults to "employment_income".

        Returns:
            np.array: [description]
        """
        system = self.simulation.tax_benefit_system
        target_entity = system.variables[target].entity.key
        wrt_entity = system.variables[wrt].entity.key
        if target_entity == wrt_entity:
            # calculating a derivative with both source and target in the same entity
            config = (wrt, delta, percent, "same-entity")
            if config not in self.bonus_sims:
                existing_var_class = system.variables[wrt].__class__

                altered_variable = type(wrt, (existing_var_class,), {})
                if not percent:
                    altered_variable.formula = (
                        lambda *args: existing_var_class.formula(*args) + delta
                    )
                else:
                    altered_variable.formula = (
                        lambda *args: existing_var_class.formula(*args)
                        * (1.0 + delta / 100)
                    )

                class bonus_ref(Reform):
                    def apply(self):
                        self.update_variable(altered_variable)

                self.bonus_sims[config] = Microsimulation(
                    self.reforms[1:] + (bonus_ref,),
                    mode=self.mode,
                    year=self.year,
                    input_year=self.input_year,
                )
            bonus_sim = self.bonus_sims[config]
            bonus_increase = bonus_sim.calc(wrt).astype(float) - self.calc(
                wrt
            ).astype(float)
            target_increase = bonus_sim.calc(target).astype(float) - self.calc(
                target
            ).astype(float)

            gradient = target_increase / bonus_increase

            return gradient
        elif (
            target_entity in ("benunit", "household")
            and wrt_entity == "person"
        ):
            # calculate the derivative for a group variable wrt a source variable, independent of other members in the group
            adult = self.calc("is_adult")
            index_in_group = (
                self.calc("person_id")
                .groupby(self.calc(f"{target_entity}_id", map_to="person"))
                .cumcount()
            )
            max_group_size = min(max(index_in_group[adult]) + 1, group_limit)

            derivative = np.empty((len(adult))) * np.nan

            for i in trange(
                max_group_size, desc="Calculating independent derivatives"
            ):
                config = (wrt, delta, percent, "group-entity", i)
                if config not in self.bonus_sims:
                    existing_var_class = system.variables[wrt].__class__

                    altered_variable = type(wrt, (existing_var_class,), {})
                    if not percent:
                        altered_variable.formula = (
                            lambda person, *args: existing_var_class.formula(
                                person, *args
                            )
                            + delta * (index_in_group == i) * adult
                        )
                    else:
                        delta /= 100
                        altered_variable.formula = (
                            lambda *args: existing_var_class.formula(*args)
                            * (1.0 + delta * (index_in_group == i) * adult)
                        )

                    class bonus_ref(Reform):
                        def apply(self):
                            self.update_variable(altered_variable)

                    self.bonus_sims[config] = Microsimulation(
                        self.reforms[1:] + (bonus_ref,),
                        mode=self.mode,
                        year=self.year,
                        input_year=self.input_year,
                    )
                bonus_sim = self.bonus_sims[config]
                bonus_increase = bonus_sim.calc(wrt).astype(float) - self.calc(
                    wrt
                ).astype(float)
                target_increase = bonus_sim.calc(
                    target, map_to="person"
                ).astype(float) - self.calc(target, map_to="person").astype(
                    float
                )
                result = target_increase / bonus_increase
                derivative[bonus_increase > 0] = result[bonus_increase > 0]

            return MicroSeries(
                derivative, weights=self.entity_weights["person"]
            )
        else:
            raise ValueError(
                "Unable to compute derivative - target variable must be from a group of or the same as the source variable"
            )

    def deriv_df(
        self, *targets, wrt="employment_income", delta=100, percent=False
    ) -> MicroDataFrame:
        wrt_entity = self.simulation.tax_benefit_system.variables[
            wrt
        ].entity.key
        df = MicroDataFrame(weights=self.entity_weights[wrt_entity])
        for target in targets:
            df[target] = self.deriv(
                target, wrt=wrt, delta=delta, percent=percent
            )
        return df
