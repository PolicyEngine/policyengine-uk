# Standard library imports
import os
import copy
import warnings
from contextlib import contextmanager, nullcontext
from importlib.metadata import version
from typing import Dict, Optional, Union, Type, List

# Third-party imports
import numpy as np
import pandas as pd

# PolicyEngine core imports
from policyengine_core.data import Dataset
from policyengine_core.enums import Enum as CoreEnum
from policyengine_core.periods import Period, period as period_
from policyengine_core.parameters import Parameter
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.simulations.simulation import (
    _uprating_index_value,
)
from policyengine_core.tools.hugging_face import download_huggingface_dataset
from policyengine_core.tracers import FullTracer, SimpleTracer

from policyengine_uk.utils.dated_reforms import read_parameter_changes
from policyengine_uk.utils.parameters import (
    check_parameter_not_removed,
    uk_fiscal_year_period,
)

# PolicyEngine UK imports
from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)
from policyengine_uk.utils.entity_ids import ENTITY_ID_VARIABLES, check_entity_ids
from policyengine_uk.utils.scenario import ConstructionReformState, Scenario
from policyengine_uk.data.economic_assumptions import (
    BEREAVEMENT_SPLIT_INPUTS,
    extend_single_year_dataset,
    reset_growthfactor_uprating,
    uprating_input_fingerprint,
)
from policyengine_uk.data.dataset_sources import materialize_gcs_dataset_url
from policyengine_uk.data.energy_price_basis import core_dataset_energy_price_basis
from policyengine_uk.data.input_dataframe import (
    dataset_from_input_dataframe,
    hold_identifiers_in,
    with_identifiers_in_each_year,
)
from policyengine_uk.data.isa_income import (
    ISA_INCOME_CONTRACT_KEY,
    MISSING_CONTRACT,
    ISA_INTEREST,
    SAVINGS_INTEREST,
    TAX_FREE_INTEREST,
    contract_envelope,
    contracts_for_years,
    has_isa_interest_detail_input,
    latest_input,
    normalized_dataset,
    read_h5_contract,
    read_object_contract,
    resolve_contracts,
    simulation_contract,
)
from policyengine_uk.data.capital_gains_projection import (
    CapitalGainsProjection,
    CGT_INPUTS,
    CGT_DATASET_INPUTS,
    CGT_INDEX_PATH,
    UnusedCapitalGainsProjectionWarning,
    add_capital_gains_projection,
    capital_gains_application_metadata,
)
from policyengine_uk.utils.dependencies import get_variable_dependencies
from policyengine_uk.utils.data_source import built_from_data
from policyengine_uk.utils.input_dataframe_export import input_dataframe
from policyengine_uk.utils.measurement_branches import (
    drop_calculated_values,
    retained_input_variables,
)
from policyengine_uk.utils.supplied_inputs import (
    SUPPLIED_INPUT_VARIABLES,
    copy_model_values,
    drop_missing_model_values,
    drop_missing_supplied_inputs,
    forget_model_values,
    forget_replaced_model_values,
    model_value_input_records,
)
from policyengine_uk.reforms import create_structural_reforms_from_parameters
from policyengine_uk.parameters.gov.simulation.labour_supply_responses.aliases import (
    canonicalize_parameter_changes,
)

from .tax_benefit_system import (
    CountryTaxBenefitSystem,
    DEFAULT_DATASET_ENV_VAR,
    parameter_reads_calendar_years,
)


def _projects_data(situation, dataset) -> bool:
    """Whether building from this source projects a dataset's later years.

    ``extend_single_year_dataset`` projects a single-year dataset from the
    parameters: one read from a file or URL (including the default dataset),
    a ``UKSingleYearDataset`` or a policyengine-core ``Dataset``. A situation,
    a DataFrame and a multi-year dataset are taken as given.
    """
    if situation is not None:
        return False
    return not isinstance(dataset, (pd.DataFrame, UKMultiYearDataset))


def _scenario_assignments(scenario) -> list:
    """A scenario's statutory-timeline changes: ``parameter_changes``, then
    each of its ``dated_reforms``, in order."""
    assignments = []
    if scenario.parameter_changes:
        assignments += read_parameter_changes(
            _canonical_parameter_paths(scenario.parameter_changes),
            calendar_years=parameter_reads_calendar_years(),
        )
    assignments += scenario.dated_assignments(order_start=len(assignments))
    return assignments


def _canonical_parameter_paths(changes: dict) -> dict:
    """Changes keyed by canonical parameter paths (labour supply aliases)."""
    return canonicalize_parameter_changes(changes)


from microdf import MicroDataFrame


class _InputKeyLog(set):
    """A simulation's record of inputs stored by a reform or scenario modifier.

    policyengine-core records each input in the simulation's
    ``_user_input_keys`` as (variable, branch, period). ``Holder._set`` adds
    the key once it has stored the value, again when it replaces one, and on
    every route: ``Simulation.set_input``, ``Holder.set_input``, a
    ``set_input`` helper, another thread. A value core does not store adds
    no key: one ``Simulation.set_input`` gets for a period after the
    variable's end, one for a neutralized variable, or one for a sub-period
    that a ``set_input`` helper skips because it already holds an input.
    This set also adds each key to every set in ``logs``: one for each
    operation being applied to the simulation, the innermost last.

    A copy or pickle of it is a plain set, so a simulation deep-copied or
    pickled while an operation runs logs nothing. A shallow copy of the
    simulation shares its record, as it shares its holders.
    """

    def __init__(self, keys=(), logs: list = ()):
        super().__init__(keys)
        self.logs = logs

    def add(self, key) -> None:
        super().add(key)
        for log in self.logs:
            log.add(key)

    def __reduce__(self):
        return set, (list(self),)


# The logs (see _InputKeyLog) of the reforms or scenario modifiers running,
# by the id of the simulation they apply to, while they do.
# Kept outside the simulation, because core's clone copies its __dict__:
# a clone or branch made while a reform runs must not log for it.
_input_key_logs: Dict[int, list] = {}


# Cache for fully-loaded, uprated, enum-pre-encoded multi-year datasets keyed
# by URL and, when selected, the CGT projection fingerprint and runtime.
# Avoids repeating HDF5 reading (0.84s), uprating (0.69s) and enum
# encoding (0.67s) on every Simulation() call after the first.
_url_dataset_cache: dict = {}
# The uprating fingerprint of current law, for each CGT projection selection
# (None: no projection), computed once. Only datasets uprated under current
# law are cached: a simulation whose uprating inputs differ builds its own.
_current_law_uprating_fingerprints: dict = {}


def _current_law_uprating_fingerprint(capital_gains_projection) -> str:
    key = (
        None
        if capital_gains_projection is None
        else capital_gains_projection.fingerprint
    )
    if key not in _current_law_uprating_fingerprints:
        system = (
            CountryTaxBenefitSystem()
            if capital_gains_projection is None
            else CountryTaxBenefitSystem(
                capital_gains_projection=capital_gains_projection
            )
        )
        _current_law_uprating_fingerprints[key] = uprating_input_fingerprint(
            system.parameters
        )
    return _current_law_uprating_fingerprints[key]


def get_default_dataset_url() -> str:
    dataset_url = os.environ.get(DEFAULT_DATASET_ENV_VAR)
    if dataset_url:
        return dataset_url
    raise ValueError(
        "Simulation() requires an explicit dataset when no situation is provided. "
        f"Pass dataset=..., or set {DEFAULT_DATASET_ENV_VAR} to opt into a default dataset."
    )


def _pre_encode_enum_columns(
    dataset: UKMultiYearDataset, tbs: "CountryTaxBenefitSystem"
) -> None:
    """Convert string enum columns in a dataset to int16 in-place.

    Run once before caching; subsequent loads use encode()'s fast integer path.
    Also stores a mapping of column name -> possible_values on each
    UKSingleYearDataset so callers can decode back to strings when needed.
    """
    for year in dataset.years:
        single_year = dataset[year]
        enum_columns: dict = {}
        for table_name in single_year.table_names:
            table = getattr(single_year, f"_{table_name}")
            for col_name in list(table.columns):
                if col_name not in tbs.variables:
                    continue
                var_def = tbs.variables[col_name]
                if var_def.value_type != CoreEnum:
                    continue
                arr = table[col_name].values
                if not isinstance(arr, np.ndarray):
                    arr = np.asarray(arr, dtype=object)
                if arr.dtype.kind in ("i", "u"):
                    # Already integer - record possible_values if not yet seen
                    enum_columns[col_name] = var_def.possible_values
                    continue
                encoded = var_def.possible_values.encode(arr)
                table[col_name] = encoded.view(np.ndarray).astype(np.int16)
                enum_columns[col_name] = var_def.possible_values
        single_year._enum_columns = enum_columns


class Simulation(CoreSimulation):
    """UK-specific simulation class for calculating tax and benefit outcomes.

    Extends the core simulation functionality with UK-specific features
    and data handling capabilities.
    """

    default_input_period: int = 2025
    default_calculation_period: int = 2025
    baseline: "Simulation"

    calculated_periods: List[str] = []
    _variable_dependencies: Dict[str, List[str]] = None
    dataset = None
    # True when built from survey or other microdata rather than a situation
    # dictionary. Variables that impute unobserved detail across a population
    # (such as months_since_last_birthday) read it through
    # utils.data_source.built_from_data; unlike the sum of weights, it stays
    # true for a region or constituency filtered from the data. The builders
    # set it, so rebuilding a simulation in place keeps it right.
    built_from_dataset: bool = False
    # True when part of the scenario is applied before data load, so the
    # parameters the data is built with may not be current law's. Such a
    # simulation neither reads nor writes the URL dataset cache.
    _scenario_before_data_load: bool = False

    def __init__(
        self,
        scenario: Optional[Scenario] = None,
        situation: Optional[Dict] = None,
        dataset: Optional[
            Union[
                pd.DataFrame,
                str,
                os.PathLike,
                UKSingleYearDataset,
                UKMultiYearDataset,
            ]
        ] = None,
        trace: bool = False,
        reform: Dict | Type[Reform] | tuple = None,
        capital_gains_projection: CapitalGainsProjection | None = None,
    ):
        """Initialize a UK simulation.

        Args:
            scenario: A Scenario object defining a modification to the simulation
            situation: A dictionary describing the situation to simulate
            dataset: Data source - can be DataFrame, URL string, or Dataset object
            trace: Whether to enable detailed tracing of calculations
            reform: A parameter-change dict, a structural Reform class, or
                a tuple of these applied in order (see Scenario.from_reform)
            capital_gains_projection: Optional common baseline gains projection,
                shared with the reform's baseline. Omit to retain GDP per capita.
        """
        self._defer_uc_health_warning = True
        self._cgt_input_provenance = {}
        self._cgt_defaulted_periods = set()
        self._cgt_calculation_depth = 0
        self._external_input_change_pending = False
        self._cgt_operation_inputs = set()
        self._cgt_warned_unused = False
        self._cgt_warning_enabled = False
        # Initialize tax-benefit rules
        self.tax_benefit_system = (
            CountryTaxBenefitSystem()
            if capital_gains_projection is None
            else CountryTaxBenefitSystem(
                capital_gains_projection=capital_gains_projection
            )
        )

        # Migrate Reform to Scenario

        if reform is not None:
            scenario = Scenario.from_reform(reform)
        # Only a construction-time reference: preserve the existing reading
        # of this scenario's single-day leftovers while rejecting unreadable
        # overrides from a user modifier's separate from_reform call.
        self._building_dated_reforms = scenario.dated_reforms if scenario else None
        self._construction_reform_state = None

        self.branch_name = "default"
        self.invalidated_caches = set()
        self.debug: bool = False
        self.trace: bool = trace
        self.tracer: SimpleTracer = SimpleTracer() if not trace else FullTracer()
        self.opt_out_cache: bool = False
        self.max_spiral_loops: int = 10
        self.memory_config = None
        self._data_storage_dir: Optional[str] = None
        self.disable_economic_assumptions: bool = False

        self.branches: Dict[str, Simulation] = {}

        # What the scenario applies before the data is built and after it. A
        # scenario is one or the other; a sum of scenarios applied at
        # different times runs each part's modifier at the part's own time.
        before_data_load, after_data_load = (
            scenario.parts_by_data_load() if scenario is not None else (None, None)
        )
        self._scenario_before_data_load = before_data_load is not None

        # A scenario's parameter changes rebuild the parameters from the
        # statutory tree, so they come before its modifier, whose edits a
        # rebuild would discard. A sum's parameter changes all come with its
        # before-load part. Without one, they come before the data is built
        # when they change what the dataset's uprating reads (a growth rate,
        # say), so the data's projected years follow them; otherwise just
        # after.
        after_parameters_before_data = (
            before_data_load is None
            and after_data_load is not None
            and _projects_data(situation, dataset)
            and self._scenario_changes_uprating_inputs(after_data_load)
        )
        if before_data_load is not None:
            self.apply_scenario_parameters(before_data_load)
            self._construction_reform_state = ConstructionReformState(self)
            if before_data_load.simulation_modifier is not None:
                before_data_load.simulation_modifier(self)
            self._construction_reform_state.observe_user_edits(self)
        elif after_parameters_before_data:
            self.apply_scenario_parameters(after_data_load)
        self._refresh_capital_gains_projection()
        # Build simulation from appropriate source
        if situation is not None:
            self.build_from_situation(situation)
        elif isinstance(dataset, (str, os.PathLike)):
            self.build_from_dataset_source(dataset)
        elif isinstance(dataset, pd.DataFrame):
            self.build_from_dataframe(dataset)
        elif isinstance(dataset, Dataset):
            self.build_from_dataset(dataset)
        elif isinstance(dataset, UKSingleYearDataset):
            self.build_from_single_year_dataset(dataset)
        elif isinstance(dataset, UKMultiYearDataset):
            self.build_from_multi_year_dataset(dataset)
        elif dataset is None:
            self.build_from_dataset_source(get_default_dataset_url())
        else:
            raise ValueError(f"Unsupported dataset type: {dataset.__class__}")

        # Parameter changes that leave the data's uprating alone come here,
        # before the steps below that read the parameters: the Universal
        # Credit rebalancing inputs and the structural reforms switched on by
        # parameters. Changes a scenario's modifier makes after data load
        # (including single-day reform-dict keys) leave the data as built.
        if after_data_load is not None and not after_parameters_before_data:
            self.apply_scenario_parameters(after_data_load)
        if self._construction_reform_state is None and self._building_dated_reforms:
            self._construction_reform_state = ConstructionReformState(self)

        # Universal Credit reform (July 2025). Needs closer integration in the baseline,
        # but adding here for ease of toggling on/off via the 'active' parameter.
        from policyengine_uk.scenarios import universal_credit_july_2025_reform

        universal_credit_july_2025_reform.simulation_modifier(self)

        # Apply structural modifiers

        self.tax_benefit_system.reset_parameter_caches()

        # Apply structural reforms based on parameters. Core applies a reform
        # to the tax-benefit system, so reforms that set inputs (such as
        # disable_simulated_benefits and adjust_budgets) reach the simulation
        # through it. Core's own constructor sets this link; this one does not
        # call it, so set it here (apply_reform also sets it for each reform).
        self.tax_benefit_system.simulation = self
        structural_reform = create_structural_reforms_from_parameters(
            self.tax_benefit_system.parameters,
            period_(self.default_input_period),
        )
        if structural_reform is not None:
            self.apply_reform(structural_reform)

        self.move_values("capital_gains", "capital_gains_before_response")
        self.move_values("employment_income", "employment_income_before_lsr")
        self.move_values(
            "employee_pension_contributions",
            "employee_pension_contributions_reported",
        )
        # Dataset totals must not mask journey-based fare policy formulas.
        # The reported amount remains available for legacy data and Wales.
        self.move_values("bus_fare_spending", "bus_fare_spending_reported")

        self.input_variables = self.get_known_variables()

        if scenario is not None:
            self.baseline = Simulation(
                scenario=None,
                situation=situation,
                dataset=dataset,
                trace=trace,
                capital_gains_projection=capital_gains_projection,
            )
        else:
            # Finish framework input invalidation before copying the baseline.
            if self._external_input_change_pending:
                drop_calculated_values(self)
                self._external_input_change_pending = False
            self.baseline = self.clone()
        self.baseline._cgt_warning_enabled = False
        self.baseline._defer_uc_health_warning = False
        self.baseline._building_dated_reforms = None
        self.baseline._construction_reform_state = None

        self.calculated_periods = []

        if after_data_load is not None:
            if self._construction_reform_state is not None:
                self._construction_reform_state.refresh_framework(self)
            if after_data_load.simulation_modifier is not None:
                with self._preserve_stored_inputs():
                    after_data_load.simulation_modifier(self)
                drop_calculated_values(self)
                self._external_input_change_pending = False
        self._refresh_capital_gains_projection()
        self._capture_cgt_supplied_inputs()
        self._cgt_warning_enabled = True
        from policyengine_uk.scenarios.uc_reform import warn_shadowed_lcwra_reform

        self._defer_uc_health_warning = False
        self._building_dated_reforms = None
        self._construction_reform_state = None
        warn_shadowed_lcwra_reform(self)

    def _refresh_capital_gains_projection(self) -> None:
        projection = self.tax_benefit_system.capital_gains_projection
        if self.disable_economic_assumptions and projection is not None:
            raise ValueError(
                "An explicit capital gains projection cannot be combined with "
                "no_economic_assumptions. Omit the projection to freeze economic assumptions."
            )
        # Scenario modifiers may edit growth or generated indices after the
        # normal processing, including plain-dict Reform overrides.
        add_capital_gains_projection(self.tax_benefit_system.parameters, projection)
        self.tax_benefit_system.reset_parameter_caches()

    @contextmanager
    def _record_stored_inputs(self):
        """Record actual stores, including overwrites and custom input routes."""
        logs = _input_key_logs.setdefault(id(self), [])
        stored = set()
        logs.append(stored)
        self._user_input_keys = getattr(self, "_user_input_keys", None) or set()
        try:
            yield stored
        finally:
            logs.pop()
            if not logs:
                del _input_key_logs[id(self)]
            # A plain set again, unless an enclosing operation is still logging.
            self._user_input_keys = set(self._user_input_keys)

    @contextmanager
    def _preserve_stored_inputs(self):
        """Name inputs an operation stores and retains, for later resets."""
        with self._record_stored_inputs() as stored:
            yield
        # Preserve the existing construction/reform input-name contract.
        # Later direct stores are also retained by retained_input_variables;
        # calculated values do not become inputs. An operation that raises
        # names nothing it stored itself (a reform it applied first has named
        # its own). Assign a new list: a clone or branch shares its parent's.
        input_variables = getattr(self, "input_variables", None)
        if input_variables is not None:
            branches = set(self._get_visible_branch_names())
            supplied = {
                name
                for name, branch, _ in stored & self._user_input_keys
                if branch in branches
            }
            added = sorted(supplied - set(input_variables))
            if added:
                self.input_variables = list(input_variables) + added

    def apply_reform(self, reform: dict | tuple | Type[Reform]) -> None:
        """Apply a runtime reform while keeping generated CGT assumptions coherent."""
        # Reforms that set inputs (disable_simulated_benefits, adjust_budgets)
        # reach the simulation through its tax-benefit system's link. A clone
        # or branch may share its parent's system, so link the system to this
        # simulation while the reform is applied, then restore the link.
        system = self.tax_benefit_system
        linked = getattr(system, "simulation", None)
        system.simulation = self
        try:
            with self._preserve_stored_inputs():
                super().apply_reform(reform)
                self._refresh_capital_gains_projection()
        finally:
            if linked is not None:
                system.simulation = linked

    @property
    def _user_input_keys(self) -> set:
        # policyengine-core's record of the simulation's inputs, kept in
        # __dict__ as core keeps it. While a reform or scenario modifier runs on
        # this simulation, a set assigned here becomes a log (see
        # _InputKeyLog), so a record core replaces mid-reform still logs: a
        # branch's, when an operation on its parent rebuilds it, or one
        # rebuilt when the system is rebound.
        try:
            return self.__dict__["_user_input_keys"]
        except KeyError:
            raise AttributeError("_user_input_keys") from None

    @_user_input_keys.setter
    def _user_input_keys(self, keys) -> None:
        logs = _input_key_logs.get(id(self))
        if logs and keys is not None:
            keys = _InputKeyLog(keys, logs)
        self.__dict__["_user_input_keys"] = keys

    @_user_input_keys.deleter
    def _user_input_keys(self) -> None:
        try:
            del self.__dict__["_user_input_keys"]
        except KeyError:
            raise AttributeError("_user_input_keys") from None

    def _invalidate_all_caches(self) -> None:
        """Rebind continuously owned reports across Core's own input replay.

        A caller's equal write is already a new input token and is pruned
        before this boundary. Only this successful synchronous Core replay
        may replace the tokens of entries that remain continuously owned.
        """
        self._prune_reported_benefit_inputs()
        ledger = getattr(self, "_reported_benefit_inputs", {})
        if not ledger:
            return super()._invalidate_all_caches()
        from policyengine_core.simulations.simulation import _value_signature

        snapshots = []
        for key, entry in ledger.items():
            holder = self.get_holder(entry["variable"])
            token = self._reported_input_token(holder, entry["branch"], entry["period"])
            if token is not entry["token"]:
                self._reported_overlay_refusal(
                    "Reported input changed before Core replay"
                )
            tiers = self._reported_genuine_tiers(
                holder, entry["branch"], entry["period"]
            )
            # Core retains memory first, otherwise disk, rather than treating
            # a computed memory shadow as the genuine disk input.
            location = (
                "memory" if "memory" in tiers else "disk" if "disk" in tiers else None
            )
            signature = (
                _value_signature(tiers[location]) if location is not None else None
            )
            if location is not None and signature is None:
                self._reported_overlay_refusal(
                    "Unsupported owned input before Core replay"
                )
            snapshots.append(
                (
                    key,
                    entry,
                    token,
                    entry["visible"],
                    entry["genuine"],
                    entry["synthetic"],
                    location,
                    signature,
                )
            )

        try:
            # The pinned Core boundary calls storage replay directly, with
            # no user formulas or input-change events. Unexpected events are
            # ambiguity, not evidence that a model report became genuine.
            result = self._reported_owned_input_events(
                [], super()._invalidate_all_caches
            )
            if getattr(self, "_reported_benefit_inputs", None) is not ledger:
                self._reported_overlay_refusal(
                    "Reported ledger replaced during Core replay"
                )
            rebound = []
            for (
                key,
                entry,
                old_token,
                visible,
                genuine,
                synthetic,
                location,
                signature,
            ) in snapshots:
                if (
                    ledger.get(key) is not entry
                    or entry["token"] is not old_token
                    or entry["visible"] is not visible
                    or entry["genuine"] is not genuine
                    or entry["synthetic"] is not synthetic
                ):
                    self._reported_overlay_refusal(
                        "Reported ownership changed during Core replay"
                    )
                holder = self.get_holder(entry["variable"])
                branch, period = entry["branch"], entry["period"]
                token = self._reported_input_token(holder, branch, period)
                actual = self._reported_genuine_tiers(holder, branch, period)
                if location is None:
                    if token is not None or actual or key in self._user_input_keys:
                        self._reported_overlay_refusal(
                            "Absent reported input appeared during Core replay"
                        )
                elif (
                    token is old_token
                    or type(token) is not tuple
                    or len(token) != 2
                    or type(token[0]) is not type(period)
                    or type(token[1]) is not frozenset
                    or token[0] != period
                    or token[1] != frozenset((location,))
                    or set(actual) != {location}
                    or _value_signature(actual[location]) != signature
                ):
                    self._reported_overlay_refusal(
                        "Owned input did not match exact Core replay"
                    )
                rebound.append((entry, token))
            # Do not leave a partially rebound ledger if a later slot fails.
            for entry, token in rebound:
                entry["token"] = token
            return result
        except BaseException as error:
            try:
                self._reported_overlay_refusal(
                    "Core reported-input replay failed or was ambiguous"
                )
            except RuntimeError as refusal:
                raise refusal from error

    def _reported_overlay_refusal(self, reason):
        """Latch ambiguity; it is never proof that a model input is genuine."""
        self._reported_benefit_observer_error = reason
        raise RuntimeError(
            f"Cannot safely synchronize reported benefit inputs: {reason}"
        )

    def _check_reported_overlay_observer(self):
        reason = getattr(self, "_reported_benefit_observer_error", None)
        if reason is not None:
            raise RuntimeError(
                f"Cannot safely synchronize reported benefit inputs: {reason}"
            )

    def _reported_observer_state(self, observer):
        frame = observer["frame"]
        events = observer["events"]
        cursor = observer["cursor"]
        from policyengine_core.simulations.simulation import _calculation_frames

        if (
            getattr(frame, "simulation", None) is not self
            or getattr(frame, "changes", None) is not events
            or type(events) is not list
            or not any(current is frame for current in _calculation_frames.get())
        ):
            self._reported_overlay_refusal(
                "Core calculation event-list identity changed"
            )
        if type(cursor) is not int or not 0 <= cursor <= len(events):
            self._reported_overlay_refusal("Core calculation event cursor is invalid")
        return events, cursor

    def _drain_reported_benefit_events(self):
        self._check_reported_overlay_observer()
        ledger = getattr(self, "_reported_benefit_inputs", {})
        for observer in tuple(getattr(self, "_reported_benefit_observers", ())):
            events, cursor = self._reported_observer_state(observer)
            for change in events[cursor:]:
                if type(change) is not tuple or len(change) != 6:
                    self._reported_overlay_refusal("Unknown Core input-event schema")
                operation, simulation, branch, variable, period, signature = change
                if (
                    type(operation) is not str
                    or operation not in ("set", "delete")
                    or not isinstance(simulation, CoreSimulation)
                    or type(branch) is not str
                    or type(variable) is not str
                    or (period is not None and not isinstance(period, Period))
                ):
                    self._reported_overlay_refusal("Unknown Core input-event identity")
                known_signature = (
                    signature is None
                    if operation == "delete"
                    else (
                        type(signature) is tuple
                        and len(signature) == 4
                        and type(signature[0]) is str
                        and type(signature[1]) is tuple
                        and all(
                            type(size) is int and size >= 0 for size in signature[1]
                        )
                        and (
                            signature[2] is None
                            or isinstance(signature[2], type)
                            and issubclass(signature[2], CoreEnum)
                        )
                        and type(signature[3]) is bytes
                    )
                )
                if not known_signature:
                    self._reported_overlay_refusal(
                        "Unknown Core input-event value signature"
                    )
                if simulation is self and operation == "delete":
                    for key, entry in list(ledger.items()):
                        if (
                            entry["variable"] == variable
                            and entry["branch"] == branch
                            and (period is None or period.contains(entry["period"]))
                        ):
                            # This includes a real no-op deletion while the
                            # displaced physical input is genuinely absent.
                            del ledger[key]
            observer["cursor"] = len(events)

    def _reported_owned_input_events(self, expected, operation):
        """Consume only the exact suffix made by one synchronous own block.

        The holder/storage operations below run no user formulas. An extra
        event or an attempt-list replacement is ambiguity, not permission to
        adopt a synthetic value as a genuine supplied input.
        """
        self._drain_reported_benefit_events()
        marks = [
            (observer, *self._reported_observer_state(observer))
            for observer in tuple(getattr(self, "_reported_benefit_observers", ()))
        ]
        try:
            result = operation()
        except BaseException as error:
            try:
                self._reported_overlay_refusal(
                    "Internal reported-input storage operation failed"
                )
            except RuntimeError as refusal:
                raise refusal from error
        for observer, events, cursor in marks:
            actual, current = self._reported_observer_state(observer)
            if actual is not events or current != cursor:
                self._reported_overlay_refusal(
                    "Internal reported-input event cursor changed"
                )
            suffix = events[cursor:]
            if len(suffix) != len(expected):
                self._reported_overlay_refusal(
                    "Unexpected event during reported-input storage"
                )
            for change, wanted in zip(suffix, expected):
                if (
                    type(change) is not tuple
                    or len(change) != 6
                    or change[1] is not self
                    or change != wanted
                ):
                    self._reported_overlay_refusal(
                        "Unverified reported-input storage event"
                    )
            observer["cursor"] = len(events)
        return result

    def _calculate(self, variable_name, period=None):
        """Observe actual attempt-local events only while reported inputs exist."""
        self._check_reported_overlay_observer()
        if not getattr(self, "_reported_benefit_inputs", None):
            return self._calculate_with_bsp_routing(variable_name, period)
        from policyengine_core.simulations.simulation import _calculation_frames

        frames = _calculation_frames.get()
        frame = next((frame for frame in frames if frame.simulation is self), None)
        if frame is None:
            self._reported_overlay_refusal(
                "Reported calculation has no actual Core frame"
            )
        observers = getattr(self, "_reported_benefit_observers", None)
        if observers is None:
            observers = self._reported_benefit_observers = []
        observer = next((item for item in observers if item["frame"] is frame), None)
        if observer is None:
            # A new outer calculation starts with a new empty attempt list.
            # Never guess a cursor into history that predates observation.
            if frame.changes:
                self._reported_overlay_refusal(
                    "Core input history predates reported observation"
                )
            if observers:
                self._reported_overlay_refusal(
                    "Reported observer escaped its Core attempt"
                )
            observer = {
                "frame": frame,
                "events": frame.changes,
                "cursor": 0,
                "users": 0,
            }
            observers.append(observer)
        self._reported_observer_state(observer)
        observer["users"] += 1
        original_error = None
        try:
            return self._calculate_with_bsp_routing(variable_name, period)
        except BaseException as error:
            original_error = error
            raise
        finally:
            try:
                # This runs BEFORE Core removes or restarts the actual frame.
                self._drain_reported_benefit_events()
            except RuntimeError as refusal:
                if original_error is not None:
                    raise refusal from original_error
                raise
            finally:
                observer["users"] -= 1
                if observer["users"] == 0:
                    observers.remove(observer)

    @staticmethod
    def _reported_input_token(holder, branch, period):
        return getattr(holder, "_user_input_storage", {}).get((branch, str(period)))

    def _reported_genuine_tiers(self, holder, branch, period):
        """Copy only genuine physical inputs, never a derived memory shadow."""
        key = (holder.variable.name, branch, period)
        if key not in getattr(self, "_user_input_keys", ()):
            return {}
        result = {}
        for location, storage in (
            ("memory", holder._memory_storage),
            ("disk", holder._disk_storage),
        ):
            if storage is not None and holder._stores_user_input(
                period, branch, location
            ):
                value = storage.get(period, branch)
                if value is not None:
                    result[location] = value.copy()
        return result

    def _prune_reported_benefit_inputs(self):
        self._drain_reported_benefit_events()
        ledger = getattr(self, "_reported_benefit_inputs", {})
        for key, entry in list(ledger.items()):
            holder = self.get_holder(entry["variable"])
            actual = self._reported_input_token(
                holder, entry["branch"], entry["period"]
            )
            if actual is not entry["token"]:
                # Every actual input write replaces the immutable record,
                # even for equal values or the same ndarray object.
                del ledger[key]
            elif actual is not None and not holder._stores_user_input(
                entry["period"], entry["branch"]
            ):
                del ledger[key]

    def _restore_reported_physical_input(self, holder, branch, period, tiers):
        """Use Core's storage/input bookkeeping with fresh write history.

        This is an exact physical-slot restore, not a baseline calculation or
        a carry-over implementation. Both genuine tiers can hold inputs.
        """
        from policyengine_core.data_storage.store_history import next_sequence_number
        from policyengine_core.simulations.simulation import _note_input_change

        for location, value in tiers.items():
            storage = (
                holder._memory_storage if location == "memory" else holder._disk_storage
            )
            if storage is None:
                raise ValueError(
                    f"Missing {location} storage while restoring {holder.variable.name}"
                )
            sequence = next_sequence_number()
            restored = value.copy()
            storage.put(
                restored, period, branch, derived=False, sequence_number=sequence
            )
            holder._record_store(period, sequence)
            holder._evict_fast_cache(period, branch)
            holder._record_input_storage(period, branch, location, is_input=True)
            self._user_input_keys.add((holder.variable.name, branch, period))
            _note_input_change(
                self, "set", holder.variable.name, period, branch, restored
            )

    def _replace_reported_benefit_input(self, entry, tiers):
        from policyengine_core.simulations.simulation import _value_signature

        self._prune_reported_benefit_inputs()
        key = (entry["variable"], entry["branch"], entry["period"])
        if getattr(self, "_reported_benefit_inputs", {}).get(key) is not entry:
            return False
        holder = self.get_holder(entry["variable"])
        period, branch = entry["period"], entry["branch"]
        # Holder.delete_arrays uses period containment in memory. Preserve
        # every other genuine contained input in its original physical tier.
        companions = []
        for name, physical_branch, other in tuple(
            getattr(self, "_user_input_keys", ())
        ):
            if (
                name == entry["variable"]
                and physical_branch == branch
                and other != period
                and period.contains(other)
            ):
                genuine = self._reported_genuine_tiers(holder, branch, other)
                if genuine:
                    companions.append((other, genuine))
        expected = [("delete", self, branch, entry["variable"], period, None)]
        for restored_period, restored_tiers in companions + [(period, tiers)]:
            for value in restored_tiers.values():
                signature = _value_signature(value)
                if signature is None:
                    self._reported_overlay_refusal(
                        "Unsupported reported-input storage value"
                    )
                expected.append(
                    ("set", self, branch, entry["variable"], restored_period, signature)
                )

        def replace():
            holder.delete_arrays(period, branch)
            for other, genuine in companions:
                self._restore_reported_physical_input(holder, branch, other, genuine)
            self._restore_reported_physical_input(holder, branch, period, tiers)

        self._reported_owned_input_events(expected, replace)
        entry["token"] = self._reported_input_token(holder, branch, period)
        return True

    def _sync_reported_benefit_inputs(self, enabled):
        self._prune_reported_benefit_inputs()
        changed = False
        for entry in tuple(getattr(self, "_reported_benefit_inputs", {}).values()):
            if entry["visible"] == enabled:
                continue
            if self._replace_reported_benefit_input(
                entry, entry["synthetic"] if enabled else entry["genuine"]
            ):
                entry["visible"] = enabled
                changed = True
        self._reported_benefit_inputs_enabled = enabled
        if changed:
            # Preserve genuine inputs; invalidate only this simulation's
            # computed values and let Core settle any stale calculation frame.
            self.drop_computed_arrays()

    @contextmanager
    def _reported_benefit_context(self, period):
        self._check_reported_overlay_observer()
        if (
            not getattr(self, "_reported_benefit_inputs", None)
            or period.unit == "eternity"
        ):
            yield
            return
        year = period.this_year
        start, count = self._reported_benefit_window
        enabled = start <= year.start.year < start + count and bool(
            self.tax_benefit_system.parameters(
                year
            ).gov.contrib.policyengine.disable_simulated_benefits
        )
        previous = getattr(self, "_reported_benefit_inputs_enabled", True)
        stack = self._reported_benefit_requests
        stack.append((year, enabled))
        try:
            self._sync_reported_benefit_inputs(enabled)
            yield
        finally:
            stack.pop()
            # A nested request returns to its caller's state. The outer call
            # leaves the stored active inputs in place for replay/export.
            # Pruning inside sync makes a genuine write during suspension win.
            self._sync_reported_benefit_inputs(previous)

    def _install_reported_benefit_inputs(self, prepared, start, count):
        self._prune_reported_benefit_inputs()
        ledger = getattr(self, "_reported_benefit_inputs", {}).copy()
        self._reported_benefit_inputs = ledger
        self._reported_benefit_window = (start, count)
        self._reported_benefit_requests = []
        self._reported_benefit_inputs_enabled = True
        for year, values in prepared.items():
            for variable, value in values.items():
                holder = self.get_holder(variable)
                period = holder._storage_period(period_(year))
                branch = self.branch_name
                key = (variable, branch, period)
                prior = ledger.get(key)
                genuine = (
                    prior["genuine"]
                    if prior is not None
                    else self._reported_genuine_tiers(holder, branch, period)
                )
                self.set_input(variable, year, value)
                token = self._reported_input_token(holder, branch, period)
                if token is None or not holder._stores_user_input(period, branch):
                    continue
                ledger[key] = {
                    "variable": variable,
                    "period": period,
                    "branch": branch,
                    "genuine": genuine,
                    "synthetic": self._reported_genuine_tiers(holder, branch, period),
                    "token": token,
                    "visible": True,
                }
        self.drop_computed_arrays()

    def delete_arrays(self, variable: str, period: Period = None) -> None:
        super().delete_arrays(variable, period)
        # Explicit deletion retires ownership even when the inactive view
        # currently holds genuine absence at that physical slot.
        ledger = getattr(self, "_reported_benefit_inputs", {})
        deleted = period_(period) if period is not None else None
        visible = set(self._get_visible_branch_names())
        for key, entry in list(ledger.items()):
            if (
                entry["variable"] == variable
                and entry["branch"] in visible
                and (deleted is None or deleted.contains(entry["period"]))
            ):
                del ledger[key]
        # From policyengine-core 3.32.27 (policyengine-core#561) the deletion
        # forgets the input records of the values it removes, but not records
        # that a population rebuild left with no stored value
        # (policyengine-core#605). Drop those too, before carry-over can refill
        # the period and input export would count the refill as an input.
        # Inspect storage after core's deletion to honour period containment
        # and the current branch, ancestor branches and default branch.
        drop_missing_supplied_inputs(self, variable)
        # A value stored later in a period whose model value (set_model_value)
        # is gone is supplied, even one equal to the deleted value.
        drop_missing_model_values(self, variable)
        if variable in CGT_DATASET_INPUTS:
            records = getattr(self, "_cgt_input_provenance", {}).get(variable, {})
            holder = self.get_holder(variable)
            for recorded_period in list(records):
                if holder.get_array(period_(recorded_period), self.branch_name) is None:
                    del records[recorded_period]

    def build_from_populations(self, populations) -> None:
        self._reported_benefit_inputs = {}
        self._reported_benefit_requests = []
        self._reported_benefit_observers = []
        self._reported_benefit_observer_error = None
        super().build_from_populations(populations)
        # The new populations hold none of the values set_model_value stored,
        # so an equal value a rebuild stores (from a situation or a frame) is
        # supplied.
        forget_model_values(self)

    def set_input(self, variable_name: str, period: Period, value) -> None:
        # What is set here is supplied, even a value equal to the model's own,
        # so forget the model value (set_model_value) of each period the call
        # stores a value for, and only those. set_model_value records its
        # value as the model's after this call.
        records = model_value_input_records(self, variable_name)
        # This depth covers every calculate call, including nongains
        # variables. A formula can write to a new branch whose own depth is
        # zero while an ancestor is calculating. Core already invalidates
        # that branch's affected dependencies; keep its unrelated caches.
        # Direct edits with every ancestor idle must refresh dependent values
        # before the next outermost calculation.
        calculation = self
        while calculation is not None and not getattr(
            calculation, "_cgt_calculation_depth", 0
        ):
            calculation = getattr(calculation, "parent_branch", None)
        external = (
            getattr(self, "input_variables", None) is not None and calculation is None
        )
        stored = set()
        failures = []

        def remember_failure(error):
            failures.append(
                (
                    error,
                    error.__traceback__,
                    error.__cause__,
                    error.__context__,
                    error.__suppress_context__,
                )
            )

        try:
            recording = (
                self._record_stored_inputs() if external else nullcontext(stored)
            )
            with recording as stored:
                try:
                    super().set_input(variable_name, period, value)
                except BaseException as error:
                    remember_failure(error)
        except BaseException as error:
            remember_failure(error)
        try:
            forget_replaced_model_values(self, variable_name, records)
        except BaseException as error:
            remember_failure(error)
        try:
            if external and stored:
                self._external_input_change_pending = True
        except BaseException as error:
            remember_failure(error)
        try:
            self._prune_reported_benefit_inputs()
        except BaseException as error:
            remember_failure(error)
        if failures:
            error, traceback, cause, context, suppression = failures[0]
            BaseException.__setattr__(
                error, "_policyengine_input_cleanup_failures", tuple(failures[1:])
            )
            try:
                raise BaseException.with_traceback(error, traceback)
            finally:
                BaseException.__setattr__(error, "__cause__", cause)
                BaseException.__setattr__(error, "__context__", context)
                BaseException.__setattr__(error, "__suppress_context__", suppression)
        # Inputs do not carry back, so give the simulation its identifiers
        # for the year the input starts in if it holds them only for later
        # years. See ``policyengine_uk.data.input_dataframe.hold_identifiers_in``.
        hold_identifiers_in(self, variable_name, period)
        if variable_name in CGT_DATASET_INPUTS:
            self._capture_cgt_supplied_inputs(variable_name, replace_period=period)

    def clone(self, *args, **kwargs) -> "Simulation":
        self._prune_reported_benefit_inputs()
        clone = super().clone(*args, **kwargs)
        clone._reported_benefit_inputs = {}
        clone._reported_benefit_requests = []
        clone._reported_benefit_observers = []
        clone._reported_benefit_observer_error = None
        for key, entry in getattr(self, "_reported_benefit_inputs", {}).items():
            copied = {
                **entry,
                "genuine": {
                    tier: value.copy() for tier, value in entry["genuine"].items()
                },
                "synthetic": {
                    tier: value.copy() for tier, value in entry["synthetic"].items()
                },
            }
            copied["token"] = clone._reported_input_token(
                clone.get_holder(entry["variable"]), entry["branch"], entry["period"]
            )
            clone._reported_benefit_inputs[key] = copied
        clone._construction_reform_state = copy.deepcopy(
            getattr(self, "_construction_reform_state", None)
        )
        copy_model_values(self, clone)
        clone._cgt_input_provenance = copy.deepcopy(
            getattr(self, "_cgt_input_provenance", {})
        )
        clone._cgt_calculation_depth = 0
        clone._cgt_operation_inputs = set()
        clone._cgt_defaulted_periods = set(getattr(self, "_cgt_defaulted_periods", ()))
        clone._isa_income_contracts = copy.deepcopy(
            getattr(self, "_isa_income_contracts", {})
        )
        # Expose a stable physical model-input state even when this clone was
        # created during an inactive caller. A direct Holder deletion before
        # its first calculate then removes a real tuple and cannot be missed.
        clone._sync_reported_benefit_inputs(True)
        return clone

    def _isa_latest_input(self, name, period, *, earlier=False):
        return latest_input(self, name, period, earlier=earlier)

    def has_isa_interest_detail_input(self, period) -> bool:
        """Whether this branch supplies an applicable ISA cash-interest detail.

        Computed caches are excluded, as in Core's carry-over input rule. A
        future detail cannot change an earlier year's aggregate.
        """
        return has_isa_interest_detail_input(self, period)

    def _isa_stored_exemption(self, period):
        # Core can store a rolling year or a longer YEAR input as given. The
        # latter carries its whole amount into a queried year; it is not a
        # sum of calendar-year flows. Use the same first definition-year
        # anchor when translating that stored amount in either direction.
        return self.calculate(TAX_FREE_INTEREST, period_(period).start.period("year"))

    def _run_formula(self, variable, population, period):
        result = super()._run_formula(variable, population, period)
        if (
            result is not None
            or variable.name != SAVINGS_INTEREST
            or period.unit != "year"
            or simulation_contract(self, period.start.year)["projection"]
            != "legacy_gross"
        ):
            return result

        # This is fallback, after Core's explicit input/abolition checks and
        # policy formulas. Preserve the old gross history even past the last
        # materialized dataset year; new additive records use Core normally.
        history = getattr(self, "_get_store_history", None)
        if callable(history):
            # Store-history tracking is available in newer Core releases;
            # the declared minimum already caches formula results without it.
            from policyengine_core.data_storage.store_history import (
                next_sequence_number,
            )

            history().record_derived(variable.name, next_sequence_number())
        source = self._isa_latest_input(variable.name, period, earlier=True)
        if source is None:
            # Core first uprates strictly earlier annual inputs, then carries
            # an input starting on the query date if there was none earlier.
            source = self._isa_latest_input(variable.name, period)
        holder = self.get_holder(variable.name)
        if source is None:
            gross = holder.default_array()
        else:
            gross = holder.get_array(source, self.branch_name)
            if (
                simulation_contract(self, source.start.year)["representation"]
                == "additive"
            ):
                gross = gross + self._isa_stored_exemption(source)
            if variable.uprating is not None:
                index = self.tax_benefit_system.parameters.get_child(variable.uprating)
                source_index = _uprating_index_value(index, source.start)
                target_index = _uprating_index_value(index, period.start)
                factor = (
                    target_index / source_index
                    if source_index not in (None, 0) and target_index is not None
                    else 1
                )
                gross = gross * factor
        return gross - self.calculate(TAX_FREE_INTEREST, period)

    @staticmethod
    def _cgt_supplied_record() -> dict:
        return {
            "status": "supplied",
            "method": "supplied_input",
            "source_period": None,
            "projection_fingerprint": None,
        }

    def _capture_cgt_supplied_inputs(
        self, variable_name: str = None, replace_period=None
    ) -> None:
        # Situation builders may write directly through Holder.set_input.
        if not hasattr(self, "populations"):
            return
        provenance = self._cgt_input_provenance
        variables = (variable_name,) if variable_name else CGT_DATASET_INPUTS
        replacement = period_(replace_period) if replace_period is not None else None
        for variable in variables:
            holder = self.get_holder(variable)
            records = provenance.setdefault(variable, {})
            for input_period in holder.get_input_periods(self.branch_name):
                key = str(input_period)
                if key not in records or input_period == replacement:
                    records[key] = self._cgt_supplied_record()

    def _cgt_present_provenance(self) -> dict:
        if not hasattr(self, "populations"):
            return {}
        records = {
            variable: {
                period: record
                for period, record in records.items()
                if self.get_holder(variable).get_array(
                    period_(period), self.branch_name
                )
                is not None
            }
            for variable, records in self._cgt_input_provenance.items()
        }
        # Neutralization returns a default before Core reads or caches arrays.
        # Keep the loaded origin separately so undoing it cannot erase history.
        for variable, period in self._cgt_defaulted_periods:
            if self._cgt_is_neutralized(variable, period_(period)):
                records.setdefault(variable, {})[period] = self._cgt_default_record()
        return records

    @staticmethod
    def _cgt_default_record() -> dict:
        return {
            "status": "default",
            "method": "default",
            "source_period": None,
            "projection_fingerprint": None,
        }

    def _cgt_is_neutralized(self, variable_name: str, period: Period) -> bool:
        variable = self.tax_benefit_system.get_variable(variable_name)
        if variable.is_neutralized:
            return True
        try:
            return bool(
                self.tax_benefit_system.parameters(period).gov.abolitions[variable_name]
            )
        except (AttributeError, KeyError):
            return False

    def _cgt_projected_record(self, method: str, source_period) -> dict:
        projection = self.tax_benefit_system.parameters.get_child(
            CGT_INDEX_PATH
        ).metadata["projection"]
        return {
            "status": "projected",
            "method": method,
            "source_period": str(source_period),
            "projection_fingerprint": projection.get("fingerprint"),
            "projection_name": projection["name"],
        }

    def _extend_dataset_with_cgt_provenance(self, dataset):
        """Retain the origin of inputs materialised by this loader only."""
        source_year = int(dataset.time_period)
        variables = [v for v in CGT_DATASET_INPUTS if v in dataset.person.columns]
        extended = extend_single_year_dataset(
            dataset, self.tax_benefit_system.parameters
        )
        # This private, in-memory annotation travels with the URL-cache value.
        # External multi-year files have no certified projection history.
        extended._cgt_extension_provenance = {
            variable: {
                str(year): self._cgt_projected_record("dataset_extension", year - 1)
                for year in extended.years
                if year > source_year
            }
            for variable in variables
        }
        return extended

    def _restore_cgt_extension_provenance(self, dataset) -> None:
        for variable, records in getattr(
            dataset, "_cgt_extension_provenance", {}
        ).items():
            restored = copy.deepcopy(records)
            if self.disable_economic_assumptions:
                # The loader reset these amounts to their base-year values.
                restored = {
                    period: {
                        "status": "unknown",
                        "method": "model_calculation",
                        "source_period": None,
                        "projection_fingerprint": None,
                    }
                    for period in restored
                }
            self._cgt_input_provenance.setdefault(variable, {}).update(restored)

    def _cgt_calculation_record(
        self, variable_name: str, period: Period, neutralized: bool = False
    ) -> dict:
        """Describe ordinary annual input uprating without inferring external history."""
        if neutralized:
            return self._cgt_default_record()
        holder = self.get_holder(variable_name)
        stored = holder.get_array(period, self.branch_name)
        record = self._cgt_input_provenance.get(variable_name, {}).get(str(period))
        if stored is not None and record is not None:
            return record
        inputs = [
            p
            for p in holder.get_input_periods(self.branch_name)
            if holder.get_array(p, self.branch_name) is not None
        ]
        if stored is not None and period in inputs:
            return self._cgt_supplied_record()
        unknown = {
            "status": "unknown",
            "method": "model_calculation",
            "source_period": None,
            "projection_fingerprint": None,
        }
        variable = holder.variable
        if (
            period.unit != "year"
            or period.size != 1
            or variable.defined_for is not None
            or variable.get_formula(period.start) is not None
            or variable.uprating != CGT_INDEX_PATH
        ):
            return unknown
        earlier = [p for p in inputs if p.unit == "year" and p.start < period.start]
        if earlier and not variable.is_neutralized:
            # Core breaks same-start ties by period end. Avoid certifying the
            # less common multi-year input route as ordinary annual uprating.
            source = max(earlier, key=lambda p: (p.start, p.stop))
            if source.size != 1:
                return unknown
            return self._cgt_projected_record("input_uprating", source)
        if inputs and not variable.is_neutralized:
            # Non-annual carry-over, or another route outside this contract.
            if any(p.start <= period.start for p in inputs):
                return unknown
        return self._cgt_default_record()

    def _warn_unused_cgt_projection(self, period: Period) -> None:
        projection = self.tax_benefit_system.capital_gains_projection
        if (
            not self._cgt_warning_enabled
            or self._cgt_warned_unused
            or self.branch_name != "default"
            or projection is None
            or period.start.year <= projection.base_year
        ):
            return
        records = self._cgt_present_provenance()
        covered = {
            variable: records.get(variable, {}).get(str(period))
            for variable in CGT_INPUTS
        }
        if any(
            record and record["status"] == "projected" for record in covered.values()
        ):
            return
        supplied = [
            variable
            for variable, record in covered.items()
            if record
            and record["status"] == "supplied"
            and (variable, str(period)) in self._cgt_operation_inputs
        ]
        if supplied:
            self._cgt_warned_unused = True
            warnings.warn(
                f"Capital gains projection {projection.name!r} was not applied to "
                f"the supplied CGT inputs for {period}: {', '.join(supplied)}. "
                "Their values remain authoritative; their historical projection "
                "is unknown. Inspect capital_gains_projection_metadata['application'] "
                "for loaded and calculated coverage.",
                UnusedCapitalGainsProjectionWarning,
                stacklevel=3,
            )

    @property
    def capital_gains_projection_metadata(self) -> dict:
        """Projection and runtime provenance for output metadata/cache fingerprints.

        Callers must additionally record dataset identity and the policy scenario.
        Pre-materialised annual inputs remain authoritative over these assumptions.
        """
        parameter = self.tax_benefit_system.parameters.get_child(CGT_INDEX_PATH)
        return {
            **copy.deepcopy(parameter.metadata["projection"]),
            "policyengine_uk_version": version("policyengine-uk"),
            "policyengine_core_version": version("policyengine-core"),
            "configuration_scope": "configured_assumptions",
            "application": capital_gains_application_metadata(
                self._cgt_present_provenance()
            ),
        }

    def _dataset_cache_key(self, source: str):
        """The URL dataset cache key for a source, or None not to cache.

        A cached dataset is already projected to later years, so it is shared
        only between simulations that project it identically: none with a
        scenario applied before data load (whose modifier can change how the
        data is read, as a structural reform re-ordering an enum does), and
        only those whose uprating inputs are current law's. A simulation with
        changed inputs (a macro scenario, ``no_economic_assumptions``, or a
        reform that changes them) neither reads nor writes the cache.
        """
        if self._scenario_before_data_load:
            return None
        system = self.tax_benefit_system
        if uprating_input_fingerprint(
            system.parameters
        ) != _current_law_uprating_fingerprint(system.capital_gains_projection):
            return None
        if system.capital_gains_projection is None:
            return source
        metadata = self.capital_gains_projection_metadata
        return (
            source,
            metadata["fingerprint"],
            metadata["policyengine_uk_version"],
            metadata["policyengine_core_version"],
        )

    def reset_calculations(self):
        retained = retained_input_variables(self)
        self._external_input_change_pending = False
        for variable in self.tax_benefit_system.variables:
            if variable not in retained:
                self.delete_arrays(variable)

    def get_known_variables(self):
        variables = []
        for variable in self.tax_benefit_system.variables:
            if len(self.get_holder(variable).get_known_periods()) > 0:
                variables.append(variable)
        return variables

    def apply_parameter_changes(self, changes: dict):
        """Rebuild the parameters with ``Scenario.parameter_changes``.

        Each change is written onto the statutory timeline (see
        ``policyengine_uk.utils.dated_reforms`` for how its period keys are
        read) and the parameters are processed as current law is.
        """
        self.apply_parameter_assignments(
            read_parameter_changes(
                _canonical_parameter_paths(changes),
                calendar_years=parameter_reads_calendar_years(),
            )
        )

    def apply_scenario_parameters(self, scenario: Scenario) -> None:
        """Rebuild the parameters with a scenario's parameter changes.

        Takes ``parameter_changes`` and then each of the scenario's
        ``dated_reforms`` in order, in one rebuild. Changes a dated reform
        leaves to the annualised parameters (single-day keys and paths the
        statutory tree does not define) are applied by the scenario's
        modifier instead.
        """
        self.apply_parameter_assignments(_scenario_assignments(scenario))

    def _scenario_changes_uprating_inputs(self, scenario: Scenario) -> bool:
        """Whether a scenario's parameter changes change the dataset uprating.

        Compares the uprating fingerprint of the parameters with the changes
        (rebuilt on a copy of the system, a rebuild the memo then serves to
        this one) with that of the parameters without them.
        """
        assignments = _scenario_assignments(scenario)
        if not assignments:
            return False
        system = self.tax_benefit_system
        return uprating_input_fingerprint(
            system.parameters_with(assignments)
        ) != uprating_input_fingerprint(system.parameters)

    def apply_parameter_assignments(self, assignments: list) -> None:
        """Rebuild the parameters with changes on the statutory timeline."""
        if not assignments:
            return
        self.tax_benefit_system.apply_parameter_assignments(assignments)
        if getattr(self, "populations", None) is not None:
            # Building from a situation or dataset can calculate values;
            # recompute them under the rebuilt parameters.
            self._invalidate_all_caches()

    def build_from_situation(self, situation: Dict) -> None:
        """Build simulation from a situation dictionary.

        Args:
            situation: Dictionary describing household composition and characteristics
        """
        self._start_new_population(built_from_dataset=False)
        self.build_from_populations(self.tax_benefit_system.instantiate_entities())
        from policyengine_core.simulations.simulation_builder import (
            SimulationBuilder,
        )  # Import here to avoid circular dependency

        builder = SimulationBuilder()
        builder.default_period = self.default_input_period
        builder.build_from_dict(self.tax_benefit_system, situation, self)
        self.has_axes = builder.has_axes
        self._capture_cgt_supplied_inputs()

        self.dataset = UKSingleYearDataset.from_simulation(
            self, fiscal_year=self.default_input_period
        )

    def build_from_dataset_source(
        self, dataset_source: Union[str, os.PathLike]
    ) -> None:
        """Build simulation from a supported dataset source string."""
        dataset_source = os.fspath(dataset_source)
        if dataset_source.startswith("hf://"):
            self.build_from_url(dataset_source)
            return
        if dataset_source.startswith("gs://"):
            cache_key = self._dataset_cache_key(dataset_source)
            if cache_key is not None and cache_key in _url_dataset_cache:
                multi_year_dataset = _url_dataset_cache[cache_key]
                self.dataset = multi_year_dataset
                self.build_from_multi_year_dataset(multi_year_dataset)
                self._restore_cgt_extension_provenance(multi_year_dataset)
                return
            dataset_file = materialize_gcs_dataset_url(dataset_source)
            self.build_from_file(dataset_file, cache_key=dataset_source)
            return
        if "://" in dataset_source:
            raise ValueError(
                "Only HuggingFace, Google Cloud Storage, and local dataset "
                "sources are supported by policyengine-uk."
            )
        self.build_from_file(dataset_source)

    def build_from_file(
        self,
        dataset_file: Union[str, os.PathLike],
        *,
        cache_key: Optional[str] = None,
    ) -> None:
        """Build simulation from a local dataset file path."""
        dataset_file = os.fspath(dataset_file)

        if UKMultiYearDataset.validate_file_path(dataset_file, False):
            multi_year_dataset = UKMultiYearDataset(dataset_file)
        elif UKSingleYearDataset.validate_file_path(dataset_file, False):
            multi_year_dataset = self._extend_dataset_with_cgt_provenance(
                UKSingleYearDataset(dataset_file)
            )
        else:
            dataset = Dataset.from_file(dataset_file, self.default_input_period)
            self.build_from_dataset(dataset)
            return

        # Convert a detached source once, then cache only the canonical object.
        # Callers holding an old gross dataset retain their original values.
        multi_year_dataset = normalized_dataset(multi_year_dataset)
        # Pre-encode string enum columns to int16 once before caching so
        # subsequent loads skip the expensive astype(str) + searchsorted path.
        _pre_encode_enum_columns(multi_year_dataset, self.tax_benefit_system)
        key = self._dataset_cache_key(cache_key) if cache_key is not None else None
        if key is not None:
            _url_dataset_cache[key] = multi_year_dataset

        self.dataset = multi_year_dataset
        self.build_from_multi_year_dataset(multi_year_dataset)
        self._restore_cgt_extension_provenance(multi_year_dataset)

    def build_from_url(self, url: str) -> None:
        """Build simulation from a HuggingFace dataset URL.

        Args:
            url: HuggingFace URL in format "hf://owner/repo/filename"

        Raises:
            ValueError: If URL is not a HuggingFace URL
        """
        if not url.startswith("hf://"):
            raise ValueError(f"Non-HuggingFace URLs are currently not supported.")

        # Return early from in-memory cache if available: skips HDF5 reading,
        # uprating and enum encoding (~2.2s on the first load).
        cache_key = self._dataset_cache_key(url)
        if cache_key is not None and cache_key in _url_dataset_cache:
            multi_year_dataset = _url_dataset_cache[cache_key]
            self.dataset = multi_year_dataset
            self.build_from_multi_year_dataset(multi_year_dataset)
            self._restore_cgt_extension_provenance(multi_year_dataset)
            return

        # Parse HuggingFace URL components
        owner, repo, filename = url.split("/")[-3:]
        if "@" in filename:
            version = filename.split("@")[-1]
            filename = filename.split("@")[0]
        else:
            version = None

        # Download dataset from HuggingFace
        dataset_file = download_huggingface_dataset(
            repo=f"{owner}/{repo}",
            repo_filename=filename,
            version=version,
        )

        self.build_from_file(dataset_file, cache_key=url)

    def build_from_dataframe(self, df: pd.DataFrame) -> None:
        """Build simulation from a pandas DataFrame.

        The frame has one row per person, in the format
        ``to_input_dataframe()`` exports. A benefit unit or household value
        sits on the row of each member, and the benefit unit or household
        takes that value. See ``policyengine_uk.data.input_dataframe`` for
        how the frame names each person's benefit unit and household.

        The simulation loads the frame as the multi-year dataset it
        describes, which ``dataset`` then holds.

        Args:
            df: DataFrame with columns in format "variable_name__time_period"
        """
        dataset, replayed, identifiers = dataset_from_input_dataframe(
            df, self.tax_benefit_system, self.default_input_period
        )
        self.build_from_multi_year_dataset(dataset)
        # Identifiers for the years the frame names them in that hold no
        # data, and so are not years of the dataset.
        for variable, time_period, values in identifiers:
            self.set_input(variable, time_period, values)
        # A dataset holds whole years only. Set each variable that the frame
        # also gives for other periods, such as months, from its columns in
        # the frame's order: a year's value spreads over the months not yet
        # set, so the order decides the months' values.
        for variable in dict.fromkeys(name for name, _, _ in replayed):
            self.delete_arrays(variable)
        for variable, time_period, values in replayed:
            if variable == SAVINGS_INTEREST:
                continue
            self.set_input(variable, time_period, values)

        # Replay savings in the incoming entry's representation. Core decides
        # which annual slots a month/span stores and what remains after prior
        # entries. Never subtract an exemption from the requested month or
        # mix a prior ordinary input into a gross residual calculation.
        def translate_stored_savings(to_gross):
            holder = self.get_holder(SAVINGS_INTEREST)
            translated = [
                (
                    stored,
                    np.array(holder.get_array(stored, self.branch_name))
                    + (1 if to_gross else -1) * self._isa_stored_exemption(stored),
                )
                for stored in holder.get_input_periods(self.branch_name)
            ]
            for stored, amount in translated:
                self.set_input(SAVINGS_INTEREST, stored, amount)

        gross_mode = None
        for variable, time_period, values in replayed:
            if variable != SAVINGS_INTEREST:
                continue
            year = period_(time_period).start.year
            contract = contracts_for_years(
                df.attrs.get(ISA_INCOME_CONTRACT_KEY, MISSING_CONTRACT), [year]
            )[year]
            incoming_gross = contract["representation"] == "legacy_gross"
            if gross_mode is not None and gross_mode != incoming_gross:
                translate_stored_savings(to_gross=incoming_gross)
            self.set_input(variable, time_period, values)
            gross_mode = incoming_gross
        if gross_mode:
            translate_stored_savings(to_gross=False)

    def to_input_dataframe(
        self, include_computed_variables: bool = False
    ) -> pd.DataFrame:
        """Export the simulation's inputs as a DataFrame that
        ``Simulation(dataset=...)`` loads back.

        Export supplied values, including overrides of variables with formulas,
        for the periods they were set for. Calculated caches and values stored
        by the model itself are not supplied inputs.
        The identifiers are also given for every whole year a column names,
        where a simulation built from the frame holds them, so that the
        default export loads back to a simulation that exports the same
        frame. See
        ``policyengine_uk.data.input_dataframe.with_identifiers_in_each_year``.

        Args:
            include_computed_variables: If True, export every stored value,
                calculated ones included, as policyengine-core does.
        """
        frame = (
            super().to_input_dataframe(include_computed_variables=True)
            if include_computed_variables
            else input_dataframe(self)
        )
        frame = with_identifiers_in_each_year(frame, self.tax_benefit_system)
        years = {
            period_(str(column).split("__", 1)[1]).start.year
            for column in frame.columns
            if "__" in str(column)
        }
        frame.attrs[ISA_INCOME_CONTRACT_KEY] = contract_envelope(
            {year: simulation_contract(self, year) for year in years}
        )
        return frame

    def build_from_dataset(self, dataset: Dataset) -> None:
        """Build simulation from a Dataset object.

        Args:
            dataset: PolicyEngine Dataset object containing simulation data
        """
        energy_price_basis = core_dataset_energy_price_basis(dataset)
        data: Dict[str, Dict[str, Union[float, int, str]]] = dataset.load_dataset()

        first_variable = data[list(data.keys())[0]]
        first_time_period = list(first_variable.keys())[0]

        def get_first_array(variable_name: str) -> np.ndarray:
            """Get the first time period's values for a variable."""
            time_period_values = data[variable_name]
            return time_period_values[first_time_period]

        # Build entity structure from IDs
        self.build_from_ids(
            *map(
                get_first_array,
                [
                    "person_id",
                    "person_benunit_id",
                    "person_household_id",
                    "benunit_id",
                    "household_id",
                ],
            )
        )

        self._isa_income_contracts = resolve_contracts(
            read_object_contract(dataset),
            read_h5_contract(getattr(dataset, "file_path", None)),
            [period_(first_time_period).start.year],
        )

        # Populations use sorted group IDs; arrays in a Core dataset follow
        # the order of that period's supplied identifier array instead.
        group_orders = {
            entity: {
                period: np.argsort(ids) for period, ids in data[f"{entity}_id"].items()
            }
            for entity in ("benunit", "household")
        }

        # Load all variable values
        for variable in data:
            for time_period in data[variable]:
                if variable not in self.tax_benefit_system.variables:
                    continue
                values = data[variable][time_period]
                entity = self.tax_benefit_system.variables[variable].entity.key
                # Leave scalars for Core to normalize and validate against
                # the population size; only arrays have a group row order.
                if entity in group_orders and np.ndim(values) > 0:
                    order = group_orders[entity].get(
                        time_period, group_orders[entity][first_time_period]
                    )
                    values = np.asarray(values)[order]
                self.set_input(variable, time_period, values)

        # Now convert to the new UKSingleYearDataset
        self.input_variables = self.get_known_variables()
        self.dataset = dataset

        dataset = UKSingleYearDataset.from_simulation(
            self, fiscal_year=first_time_period, energy_price_basis=energy_price_basis
        )
        multi_year_dataset = self._extend_dataset_with_cgt_provenance(dataset)

        self.dataset = multi_year_dataset
        self.build_from_multi_year_dataset(multi_year_dataset)
        self._restore_cgt_extension_provenance(multi_year_dataset)

    def build_from_single_year_dataset(self, dataset: UKSingleYearDataset) -> None:
        """Build simulation from a single-year UK dataset.

        Args:
            dataset: UKSingleYearDataset containing one year of data
        """

        dataset = self._extend_dataset_with_cgt_provenance(dataset)
        _pre_encode_enum_columns(dataset, self.tax_benefit_system)
        self.dataset = dataset
        self.build_from_multi_year_dataset(dataset)
        self._restore_cgt_extension_provenance(dataset)

    def build_from_multi_year_dataset(self, dataset: UKMultiYearDataset) -> None:
        """Build simulation from a multi-year UK dataset.

        Args:
            dataset: UKMultiYearDataset containing multiple years of data
        """
        if self.disable_economic_assumptions:
            dataset = dataset.copy()
            # The reset copies base-year values positionally. Align only the
            # copied group tables first when their row order differs by year.
            for year in dataset.years:
                for entity in ("benunit", "household"):
                    table = getattr(dataset[year], entity)
                    order = np.argsort(table[f"{entity}_id"].to_numpy())
                    setattr(dataset[year], entity, table.iloc[order])
            reset_growthfactor_uprating(dataset)

        # The legacy gross projection/reset must finish before conversion.
        # Work on detached tables: a cached or caller-owned source is reusable.
        dataset = normalized_dataset(dataset)

        # Ensure enum columns are encoded and _enum_columns is populated so
        # that .person/.benunit/.household properties can decode back to strings.
        if not any(dataset[y]._enum_columns for y in dataset.years):
            _pre_encode_enum_columns(dataset, self.tax_benefit_system)
        # Use first year to establish entity structure
        first_year = dataset[dataset.years[0]]
        self.build_from_ids(
            first_year.person.person_id,
            first_year.person.person_benunit_id,
            first_year.person.person_household_id,
            first_year.benunit.benunit_id,
            first_year.household.household_id,
        )
        self._isa_income_contracts = {
            year: copy.deepcopy(dataset[year].isa_income_contract)
            for year in dataset.years
        }

        # Load variable values for all years
        for year in dataset.years:
            for entity, table in zip(dataset[year].table_names, dataset[year].tables):
                if entity in ("benunit", "household"):
                    # Align each year's group inputs to the sorted population
                    # without reordering the caller's table or the people.
                    table = table.iloc[np.argsort(table[f"{entity}_id"].to_numpy())]
                for variable in table.columns:
                    if variable not in self.tax_benefit_system.variables:
                        continue
                    self.set_input(variable, year, table[variable])

        # Retain the dataset actually loaded, including the copied base amounts
        # and price declaration when economic assumptions were disabled.
        self.dataset = dataset
        if self.disable_economic_assumptions:
            # The loader changed these future amounts even for an external
            # multi-year dataset; they are no longer unchanged supplied inputs.
            for variable in CGT_DATASET_INPUTS:
                for year in dataset.years[1:]:
                    if variable in dataset[year].person.columns:
                        self._cgt_input_provenance.setdefault(variable, {})[
                            str(year)
                        ] = {
                            "status": "unknown",
                            "method": "model_calculation",
                            "source_period": None,
                            "projection_fingerprint": None,
                        }

    def _start_new_population(self, built_from_dataset: bool) -> None:
        """Record the new population's source, and drop what the simulation
        cached for the previous one, so rebuilding in place (e.g. a clone)
        never reads arrays sized for the old population."""
        self._reported_benefit_inputs = {}
        self._reported_benefit_requests = []
        self._reported_benefit_observers = []
        self._reported_benefit_observer_error = None
        self.built_from_dataset = built_from_dataset
        if getattr(self, "_fast_cache", None) is not None:
            self._fast_cache = {}
        if getattr(self, "_user_input_keys", None) is not None:
            # A clone shares this set with its original, so replace it.
            self._user_input_keys = set()
        # Origins and warning observations belong to the replaced population.
        # Use new containers so rebuilding a clone cannot alter its original.
        self._cgt_input_provenance = {}
        self._cgt_defaulted_periods = set()
        self._cgt_operation_inputs = set()
        self._cgt_warned_unused = False
        self._isa_income_contracts = {}

    def build_from_ids(
        self,
        person_id: np.ndarray,
        person_benunit_id: np.ndarray,
        person_household_id: np.ndarray,
        benunit_id: np.ndarray,
        household_id: np.ndarray,
    ) -> None:
        """Build simulation entities from ID arrays.

        Args:
            person_id: Array of person IDs
            person_benunit_id: Array mapping persons to benefit units
            person_household_id: Array mapping persons to households
            benunit_id: Array of benefit unit IDs
            household_id: Array of household IDs

        Warns:
            EntityIdWarning: If an ID is not a whole number, or is outside the
                range of the variable that stores it, so that the stored ID
                differs from the one given.
        """
        # Every data source (DataFrame, dataset, file, URL) builds through here.
        self._start_new_population(built_from_dataset=True)
        from policyengine_core.simulations.simulation_builder import (
            SimulationBuilder,
        )  # Import here to avoid circular dependency

        # The callers store these columns as the variables' values after
        # building the entities, and exports and rebuilds read them from there.
        # The populations below take the arrays as given.
        for variable_name, ids in zip(
            ENTITY_ID_VARIABLES,
            (
                person_id,
                person_benunit_id,
                person_household_id,
                benunit_id,
                household_id,
            ),
        ):
            check_entity_ids(self.tax_benefit_system.variables[variable_name], ids)

        builder = SimulationBuilder()
        builder.populations = self.tax_benefit_system.instantiate_entities()

        # Declare entities
        builder.declare_person_entity("person", person_id)
        builder.declare_entity("benunit", np.unique(benunit_id))
        builder.declare_entity("household", np.unique(household_id))

        # Link persons to benefit units and households
        builder.join_with_persons(
            builder.populations["benunit"],
            person_benunit_id,
            np.array(["member"] * len(person_benunit_id)),
        )
        builder.join_with_persons(
            builder.populations["household"],
            person_household_id,
            np.array(["member"] * len(person_household_id)),
        )

        self.build_from_populations(builder.populations)

    def move_values(self, variable_donor: str, variable_target: str) -> None:
        """Move values from one variable to another across all branches.

        Used for behavioral response modeling where original values need
        to be preserved.

        Args:
            variable_donor: Variable to move values from
            variable_target: Variable to move values to
        """
        for simulation in list(self.branches.values()) + [self]:
            holder = simulation.get_holder(variable_donor)
            for known_period in holder.get_known_periods():
                array = holder.get_array(known_period)
                simulation.set_input(variable_target, known_period, array)
                if (
                    variable_donor in CGT_DATASET_INPUTS
                    and variable_target in CGT_INPUTS
                ):
                    origin = simulation._cgt_input_provenance.get(
                        variable_donor, {}
                    ).pop(str(known_period), self._cgt_supplied_record())
                    simulation._cgt_input_provenance.setdefault(variable_target, {})[
                        str(known_period)
                    ] = copy.deepcopy(origin)
                holder.delete_arrays(known_period)

    def calculate_all(self, year: int) -> None:
        person, benunit, household = (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )
        period = str(year)
        for variable in self.tax_benefit_system.variables.values():
            entity = variable.entity.key
            result = self.calculate(variable.name, period).values
            if entity == "person":
                person[variable.name] = result
            elif entity == "benunit":
                benunit[variable.name] = result
            elif entity == "household":
                household[variable.name] = result

        person = MicroDataFrame(person, weights="person_weight")
        benunit = MicroDataFrame(benunit, weights="benunit_weight")
        household = MicroDataFrame(household, weights="household_weight")

        return UKSingleYearDataset(
            person=person,
            benunit=benunit,
            household=household,
            fiscal_year=year,
        )

    def _calculate_with_bsp_routing(self, variable_name: str, period: Period = None):
        # Core requires an indexed input to have no formula. Keep the legacy
        # CPI declaration, but carry split dataset BSP nominally after the
        # materialized horizon, including through Core's monthly conversion.
        if (
            variable_name == "bsp_reported"
            and period is not None
            and period.unit == "year"
            and period.size == 1
            and built_from_data(self)
        ):
            variable = self.tax_benefit_system.get_variable(variable_name)
            holder = self.get_holder(variable_name)
            inputs = holder.get_input_periods(self.branch_name)
            if (
                not variable.formulas
                and not variable.is_neutralized
                and variable.uprating
                == "gov.economic_assumptions.indices.obr.consumer_price_index"
                and period not in inputs
            ):
                source = max(
                    (
                        known
                        for known in inputs
                        if known.unit == "year" and known.start < period.start
                    ),
                    key=lambda known: (known.start, known.stop),
                    default=None,
                )
                if source is not None:
                    split = all(
                        source
                        in self.get_holder(name).get_input_periods(self.branch_name)
                        for name in BEREAVEMENT_SPLIT_INPUTS
                    )
                    # Track both dependencies even when either input is absent.
                    # Calculated defaults do not declare a completed split.
                    for name in BEREAVEMENT_SPLIT_INPUTS:
                        self.calculate(name, source)
                    if split:
                        return self.calculate(variable_name, source)
        return super()._calculate(variable_name, period)

    def calculate(
        self,
        variable_name: str = None,
        period: str = None,
        map_to: str = None,
        decode_enums: bool = False,
    ):
        self._check_reported_overlay_observer()
        if self._cgt_calculation_depth == 0 and self._external_input_change_pending:
            self._external_input_change_pending = False
            drop_calculated_values(self)
        if variable_name is None:
            return self.calculate_all()
        tracer: SimpleTracer = self.tracer
        if len(tracer.stack) == 0:
            # Only decode enums to string values when we're not within
            # the simulation tree.
            decode_enums = True

        if period is None:
            period = self.default_calculation_period

        period = period_(period)

        with self._reported_benefit_context(period):
            projection = self.tax_benefit_system.capital_gains_projection
            if projection is not None and variable_name in CGT_INPUTS:
                holder = self.get_holder(variable_name)
                annual_period = period.this_year
                if holder.get_array(annual_period, self.branch_name) is None:
                    earlier_inputs = [
                        p
                        for p in holder.get_input_periods(self.branch_name)
                        if p.unit == "year"
                        and p.start < annual_period.start
                        and holder.get_array(p, self.branch_name) is not None
                    ]
                    if earlier_inputs:
                        source_year = max(p.start.year for p in earlier_inputs)
                        projection.validate_span(source_year, annual_period.start.year)

            if variable_name in SUPPLIED_INPUT_VARIABLES:
                # Rebuilding the populations leaves the input records of the
                # replaced holders behind (policyengine-core#605). Forget a record
                # whose stored value is gone before the engine can refill the
                # period with a carried-over value that the record would pass off
                # as supplied.
                drop_missing_supplied_inputs(self, variable_name)

            outer_calculation = self._cgt_calculation_depth == 0
            if outer_calculation:
                self._cgt_operation_inputs = set()
            record = None
            neutralized = False
            if variable_name in CGT_INPUTS:
                neutralized = self._cgt_is_neutralized(variable_name, period)
                record = self._cgt_calculation_record(
                    variable_name, period, neutralized
                )
            self._cgt_calculation_depth += 1
            try:
                result = super().calculate(
                    variable_name, period, map_to=map_to, decode_enums=decode_enums
                )
                if record is not None:
                    if neutralized:
                        self._cgt_defaulted_periods.add((variable_name, str(period)))
                    else:
                        self._cgt_input_provenance.setdefault(variable_name, {})[
                            str(period)
                        ] = record
                    self._cgt_operation_inputs.add((variable_name, str(period)))
            finally:
                self._cgt_calculation_depth -= 1
            if outer_calculation and self._cgt_operation_inputs:
                for input_period in sorted({p for _, p in self._cgt_operation_inputs}):
                    self._warn_unused_cgt_projection(period_(input_period))
            return result

    def apply_dynamics(self, year: int):
        """Apply dynamics to the simulation for a specific year.

        Args:
            year: Year to apply dynamics for
        """
        # Apply OBR labour supply dynamics if enabled
        from policyengine_uk.dynamics.labour_supply import (
            apply_labour_supply_responses,
        )

        return apply_labour_supply_responses(self, year=str(year))

    def get_variable_dependencies(self, variable_name: str, depth: int = 1):
        if self._variable_dependencies is None:
            self._variable_dependencies = {}
            self._example_simulation = Simulation(
                situation={
                    "age": 30,
                },
                trace=True,
            )
            self._example_simulation.calculate("hbai_household_net_income")
            for variable in self._example_simulation.tax_benefit_system.variables:
                try:
                    dependencies = get_variable_dependencies(
                        variable, self._example_simulation
                    )
                    self._variable_dependencies[variable] = dependencies
                except Exception as e:
                    self._variable_dependencies[variable] = []

        if variable_name not in self._variable_dependencies:
            raise ValueError(
                f"Variable '{variable_name}' not found in simulation dependencies."
            )
        dependencies = self._variable_dependencies[variable_name]

        if depth <= 1:
            return dependencies

        all_dependencies = set(dependencies)
        for dep in dependencies:
            try:
                sub_dependencies = self.get_variable_dependencies(dep, depth - 1)
                all_dependencies.update(sub_dependencies)
            except ValueError:
                continue
        return list(all_dependencies)

    def compare(
        self,
        other: "Simulation",
        variables: list[str] = None,
        period: str = None,
        change_only: bool = False,
    ):
        """Compare two simulations for a specific variable list.

        Args:
            other: Another Simulation instance to compare against
            variables: List of variable names to compare. If None, compares all variables.

        Returns:
            DataFrame with comparison results
        """

        if variables is None:
            variables = self.input_variables + [
                "hbai_household_net_income",
            ]

        df_self = self.calculate_dataframe(variables, period=period)
        df_other = other.calculate_dataframe(variables, period=period)

        df_combined = pd.concat([df_self, df_other], axis=1, keys=["self", "other"])
        # Reset columns, then order by variable name first then self/other
        df_combined.columns = [f"{var}_{entity}" for entity, var in df_combined.columns]
        # Add change where applicable (numeric only)
        for variable in variables:
            self_col = f"{variable}_self"
            other_col = f"{variable}_other"
            try:
                df_combined[f"{variable}_change"] = (
                    df_combined[other_col] - df_combined[self_col]
                )
            except:
                # For other data types, use XOR
                df_combined[f"{variable}_change"] = (
                    df_combined[other_col] != df_combined[self_col]
                )
        columns = []

        for variable in variables:
            columns.extend(
                [
                    f"{variable}_self",
                    f"{variable}_other",
                    f"{variable}_change",
                ]
            )

        if change_only:
            variables_to_include = []
            for variable in variables:
                if df_combined[f"{variable}_change"].mean() > 0:
                    variables_to_include.extend(
                        [
                            f"{variable}_self",
                            f"{variable}_other",
                            f"{variable}_change",
                        ]
                    )
            columns = variables_to_include
        return df_combined[columns]
