import openfisca_uk
from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_core.periods import period
import pandas as pd
from openfisca_core.simulation_builder import SimulationBuilder
import numpy as np
import warnings
import microdf as mdf
import functools
from typing import List, Tuple, Union, Dict
from microdf.generic import MicroDataFrame, MicroSeries
from openfisca_core.populations import Population
import pandas as pd
import openfisca_uk
from openfisca_uk.entities import *
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.model_api import *
import numpy as np
import microdf as mdf
from tqdm import trange
import warnings
from openfisca_uk.tools.parameters import backdate_parameters
from openfisca_uk.tools.general import carried_over
from openfisca_uk_data import SynthFRS, DATASETS
import yaml
from pathlib import Path


with open(Path(__file__).parent / "datasets.yml") as f:
    datasets = yaml.safe_load(f)
    DEFAULT_DATASET = list(
        filter(lambda ds: ds.name == datasets["default"], DATASETS)
    )[0]


warnings.filterwarnings("ignore")

np.random.seed(0)


class IndividualSim:
    def __init__(self, *reforms, year=2020):
        self.year = year
        self.reforms = reforms
        self.system = openfisca_uk.CountryTaxBenefitSystem()
        self.sim_builder = SimulationBuilder()
        self.entities = {var.key: var for var in self.system.entities}
        self.apply_reforms(self.reforms)
        self.situation_data = {"people": {}, "benunits": {}, "households": {}}
        self.varying = False
        self.num_points = None

    def build(self):
        self.sim = self.sim_builder.build_from_entities(
            self.system, self.situation_data
        )

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

    def add_data(
        self,
        entity="people",
        name=None,
        input_period=None,
        auto_period=True,
        **kwargs,
    ):
        input_period = input_period or self.year
        entity_plural = self.entities[entity].plural
        if name is None:
            name = (
                entity + "_" + str(len(self.situation_data[entity_plural]) + 1)
            )
        if auto_period:
            data = {}
            for var, value in kwargs.items():
                try:
                    def_period = self.system.get_variable(
                        var
                    ).definition_period
                    if def_period in ["eternity", "year"]:
                        input_periods = [input_period]
                    else:
                        input_periods = period(input_period).get_subperiods(
                            def_period
                        )
                    data[var] = {
                        str(subperiod): value for subperiod in input_periods
                    }
                except:
                    data[var] = value
        self.situation_data[entity_plural][name] = data

    def add_person(self, **kwargs):
        self.add_data(entity="person", **kwargs)

    def add_benunit(self, **kwargs):
        self.add_data(entity="benunit", name="benunit", **kwargs)

    def add_household(self, **kwargs):
        self.add_data(entity="household", name="household", **kwargs)

    def get_entity(self, name):
        entity_type = [
            entity
            for entity in self.entities.values()
            if name in self.situation_data[entity.plural]
        ][0]
        return entity_type

    def get_group(self, entity, name):
        containing_entity = [
            group
            for group in self.situation_data[entity.plural]
            if name in self.situation_data[entity.plural][group]["adults"]
            or name in self.situation_data[entity.plural][group]["children"]
        ][0]
        return containing_entity

    def calc(self, var, period=None, target=None, index=None):
        if not hasattr(self, "sim"):
            self.build()
        period = period or self.year
        entity = self.system.variables[var].entity
        if target is not None:
            target_entity = self.get_entity(target)
            if target_entity.key != entity.key:
                target = self.get_group(entity, target)
        try:
            result = self.sim.calculate(var, period)
        except:
            try:
                result = self.sim.calculate_add(var, period)
            except:
                result = self.sim.calculate_divide(var, period)
        if self.varying:
            result = result.reshape(
                (self.num_points, len(self.situation_data[entity.plural]))
            ).transpose()
        members = list(self.situation_data[entity.plural])
        if index is not None:
            index = min(len(members) - 1, index)
        if target is not None:
            index = members.index(target)
        if target is not None or index is not None:
            return result[index]
        return result

    def calc_deriv(
        self,
        var,
        wrt="employment_income",
        period=None,
        var_target=None,
        wrt_target=None,
    ):
        period = period or self.year
        y = self.calc(var, period=period, target=var_target)
        x = self.calc(wrt, period=period, target=wrt_target)
        try:
            y = y.squeeze()
        except:
            pass
        try:
            x = x.squeeze()
        except:
            pass
        x = x.astype(np.float32)
        y = y.astype(np.float32)
        assert (
            len(y) > 1 and len(x) > 1
        ), "Simulation must vary on an axis to calculate derivatives."
        deriv = (y[1:] - y[:-1]) / (x[1:] - x[:-1])
        deriv = np.append(deriv, deriv[-1])
        return deriv

    def calc_mtr(
        self,
        target="household_net_income",
        wrt="employment_income",
        wrt_target=None,
        var_target=None,
    ):
        return 1 - self.calc_deriv(
            target, wrt=wrt, wrt_target=wrt_target, var_target=var_target
        )

    def reset_vary(self):
        del self.situation_data["axes"]
        self.varying = False
        self.num_points = None

    def vary(self, var, min=0, max=200000, step=100, index=0, period=None):
        period = period or self.year
        if "axes" not in self.situation_data:
            self.situation_data["axes"] = [[]]
        count = int((max - min) / step)
        self.situation_data["axes"][0] += [
            {
                "count": count,
                "name": var,
                "min": min,
                "max": max,
                "period": period,
                "index": index,
            }
        ]
        self.build()
        self.varying = True
        self.num_points = count


class Microsimulation:
    def __init__(
        self,
        *reforms: Tuple[Reform],
        year: int = None,
        dataset=DEFAULT_DATASET,
    ):
        self.dataset = dataset
        self.passed_reforms = reforms
        if dataset == SynthFRS and len(SynthFRS.years) == 0:
            SynthFRS.save()
        if year is None:
            self.year = max(dataset.years)
        else:
            self.year = year
        self.reforms = (
            *reforms,
            backdate_parameters(),
        )
        self.load_dataset(dataset, self.year)
        self.entity_weights = dict(
            person=self.calc("person_weight", self.year, weighted=False),
            benunit=self.calc("benunit_weight", self.year, weighted=False),
            household=self.calc("household_weight", self.year, weighted=False),
        )
        self.bonus_sims = {}
        self.simulation.max_spiral_loops = 20

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
        period: Union[str, int] = 2021,
        weighted: bool = True,
        map_to: str = None,
        how: str = None,
        dp: int = 2,
    ) -> MicroSeries:
        if period is None:
            period = self.year
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
            arr = arr.round(dp)
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
        if period is None:
            period_kwarg = {}
        else:
            period_kwarg = {"period": period}
        for var in vars:
            df[var] = self.calc(var, **period_kwarg, map_to=entity)
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

    def load_dataset(self, dataset, year: int) -> None:
        data = dataset.load(year)
        year = str(year)
        self.system = openfisca_uk.CountryTaxBenefitSystem()

        class carry_over_by_default(Reform):
            def apply(s):
                for var in data.keys():
                    if var in self.system.variables:
                        var_cls = type(self.system.variables[var])
                        s.update_variable(carried_over(var_cls))

        self.apply_reforms((carry_over_by_default, *self.reforms))
        builder = SimulationBuilder()
        builder.create_entities(self.system)
        self.relations = {
            "person": np.array(data["person_id"]),
            "benunit": np.array(data["benunit_id"]),
            "household": np.array(data["household_id"]),
            "person-benunit": np.array(data["person_benunit_id"]),
            "person-household": np.array(data["person_household_id"]),
        }
        builder.declare_person_entity("person", np.array(data["person_id"]))
        benunits = builder.declare_entity(
            "benunit", np.array(data["benunit_id"])
        )
        households = builder.declare_entity(
            "household", np.array(data["household_id"])
        )
        person_roles = np.array(np.array(data["role"])).astype(str)
        builder.join_with_persons(
            benunits, np.array(data["person_benunit_id"]), person_roles
        )  # define person-benunit memberships
        builder.join_with_persons(
            households, np.array(data["person_household_id"]), person_roles
        )  # define person-household memberships
        model = builder.build(self.system)
        skipped = []
        for variable in data.keys():
            if variable in self.system.variables:
                values = np.array(data[variable])
                target_dtype = self.system.variables[variable].value_type
                if target_dtype in (Enum, str):
                    values = values.astype(str)
                else:
                    values = values.astype(target_dtype)
                try:
                    model.set_input(variable, year, values)
                except:
                    skipped += [variable]
        if skipped:
            warnings.warn(
                f"Incomplete initialisation: skipped {len(skipped)} variables:"
            )
        self.simulation = model
        data.close()

    def deriv(
        self,
        target="tax",
        wrt="employment_income",
        delta=100,
        percent=False,
        group_limit=5,
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
                self.bonus_sims[config] = Microsimulation(
                    self.passed_reforms,
                    dataset=self.dataset,
                    year=self.year,
                )
                original_values = (
                    self.bonus_sims[config].calc(wrt, self.year).values
                )
                if not percent:
                    self.bonus_sims[config].simulation.set_input(
                        wrt, self.year, original_values + delta
                    )
                else:
                    self.bonus_sims[config].simulation.set_input(
                        wrt, self.year, original_values * (1 + delta)
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

            for i in range(max_group_size):
                config = (wrt, delta, percent, "group-entity", i)
                if config not in self.bonus_sims:
                    self.bonus_sims[config] = Microsimulation(
                        self.passed_reforms,
                        dataset=self.dataset,
                        year=self.year,
                    )
                    original_values = (
                        self.bonus_sims[config].calc(wrt, self.year).values
                    )
                    existing_var_class = system.variables[wrt].__class__

                    altered_variable = type(wrt, (existing_var_class,), {})
                    if not percent:
                        self.bonus_sims[config].simulation.set_input(
                            wrt,
                            self.year,
                            original_values
                            + delta * (index_in_group == i) * adult,
                        )
                    else:
                        self.bonus_sims[config].simulation.set_input(
                            wrt,
                            self.year,
                            original_values
                            * (1 + delta * (index_in_group == i) * adult),
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
