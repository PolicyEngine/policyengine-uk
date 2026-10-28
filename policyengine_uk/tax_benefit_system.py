# Standard library imports
import copy
import logging
from collections import OrderedDict
from dataclasses import replace
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# PolicyEngine core imports
from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import (
    uprate_parameters,
)
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.variables import Variable

# PolicyEngine UK imports
from policyengine_uk.entities import BenUnit, Household, Person
from policyengine_uk.data.capital_gains_projection import (
    CapitalGainsProjection,
    add_capital_gains_projection,
    check_capital_gains_projection_parameter,
)
from policyengine_uk.parameters.gov.contrib.create_private_pension_uprating import (
    add_private_pension_uprating_factor,
)
from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    add_triple_lock,
)
from policyengine_uk.parameters.gov.dwp.housing_benefit.allowances.create_pension_age_allowances import (
    project_pension_age_allowances,
)
from policyengine_uk.parameters.gov.dwp.pension_credit.savings_credit.create_savings_credit_threshold import (
    project_savings_credit_threshold,
)
from policyengine_uk.parameters.gov.dwp.universal_credit.rebalancing.create_health_element_uprating import (
    add_uc_health_element_uprating,
)
from policyengine_uk.parameters.gov.dwp.universal_credit.rebalancing.create_standard_allowance_uprating import (
    add_uc_standard_allowance_uprating,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_september_cpi_uprating import (
    add_september_cpi_uprating,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_earnings_uprating import (
    add_earnings_uprating,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    create_economic_assumption_indices,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_statutory_uprating_inputs import (
    add_statutory_uprating_inputs,
)
from policyengine_uk.parameters.gov.hmrc.create_threshold_indexation import (
    add_threshold_indexation,
)
from policyengine_uk.parameters.gov.economic_assumptions.lag_average_earnings import (
    add_lagged_earnings,
)
from policyengine_uk.parameters.gov.economic_assumptions.lag_cpi import (
    add_lagged_cpi,
)
from policyengine_uk.parameters.gov.simulation.labour_supply_responses.aliases import (
    add_lsr_deprecation_aliases,
    canonicalize_lsr_parameter_path,
)
from policyengine_uk.utils.benefit_unit import CLAIMANT_OR_PARTNER_AWARDS
from policyengine_uk.utils.dated_reforms import (
    BACKDATED_FROM,
    CALENDAR_YEAR_SERIES,
    LegacyOverride,
    ParameterAssignment,
    Timeline,
    apply_legacy_overrides,
    copy_timelines,
    graft_missing_nodes,
    requires_projection,
    snapshot_timelines,
    tree_defines,
    write_assignment,
)
from policyengine_uk.utils.parameters import (
    add_removed_parameter_aliases,
    backdate_parameters,
    convert_to_fiscal_year_parameters,
)

from policyengine_uk.utils.ni_parameter_scales import (
    LegacyNIParameter,
    canonical_descendants,
    canonical_ni_processing,
    validate_ni_scale_compatibility,
    canonical_ni_uprating_references,
    canonicalize_ni_parameter_path,
)

logger = logging.getLogger(__name__)


def _install_parameters(system, parameters: ParameterNode) -> None:
    # A Core Reform delegates unknown instance methods to its baseline. Keep
    # this orchestration local and call the public base operation explicitly:
    # Reform.modify_parameters would also start from the baseline's tree.
    TaxBenefitSystem.modify_parameters(system, lambda _: parameters)


# Module constants
COUNTRY_DIR = Path(__file__).parent
DEFAULT_DATASET_ENV_VAR = "POLICYENGINE_UK_DEFAULT_DATASET"

# Cache for fully-processed parameter tree, so convert_to_fiscal_year_parameters
# (22,538 param.update() calls) only runs once per process.
_processed_parameters_cache = None
# The parameters as loaded from the YAML files, before processing: each
# parameter's statutory values at their legal dates. Reforms are written
# onto a copy of this tree.
_statutory_parameters_cache = None
# Each parameter's timeline in the cached processed tree after projection
# (uprating, indexation and the other generated series) and, for gov
# parameters, before fiscal-year annualisation, by name.
_projected_timelines_cache = None


# The steps that generate parameters from others, in order. Each may read
# what the steps before it generate.
GENERATION_STEPS = (
    add_private_pension_uprating_factor,
    add_lagged_earnings,
    add_lagged_cpi,
    add_statutory_uprating_inputs,
    add_earnings_uprating,
    add_triple_lock,
    add_september_cpi_uprating,
    create_economic_assumption_indices,
    project_savings_credit_threshold,
    project_pension_age_allowances,
    add_threshold_indexation,
    add_uc_standard_allowance_uprating,
    add_uc_health_element_uprating,
    add_lsr_deprecation_aliases,
)


def _add_generated_parameters(
    parameters: ParameterNode,
    generated: Optional[List[ParameterAssignment]] = None,
    unreformed: Optional[ParameterNode] = None,
    enacted: Optional[ParameterNode] = None,
) -> ParameterNode:
    """Run the generation steps, writing changes to generated parameters.

    Each change in ``generated`` is written onto its parameter just after
    the step that generates it, so the later steps, and uprating, read it.
    ``enacted`` supplies the YAML as loaded, before any modifier edits, for
    the Pension Credit and Housing Benefit projection bases.
    """
    pending = list(generated or [])
    for step in GENERATION_STEPS:
        if step in (project_savings_credit_threshold, project_pension_age_allowances):
            parameters = step(parameters, unreformed=unreformed, enacted=enacted)
        else:
            parameters = step(parameters)
        if pending:
            defines = tree_defines(parameters)
            for assignment in [a for a in pending if defines(a.path)]:
                write_assignment(parameters.get_child(assignment.path), assignment)
                pending.remove(assignment)
    if pending:
        raise ValueError(
            "Could not find the parameter "
            + ", ".join(sorted({assignment.path for assignment in pending}))
            + "."
        )
    return parameters


def process_parameter_tree(
    parameters: ParameterNode,
    unreformed: Optional[ParameterNode] = None,
    annualise: bool = True,
    generated: Optional[List[ParameterAssignment]] = None,
    enacted: Optional[ParameterNode] = None,
) -> Tuple[ParameterNode, Dict[str, Timeline]]:
    """Project and annualise a statutory parameter tree.

    Applies, in order:
    - private pension uprating factors
    - lagged earnings and CPI indices
    - statutory uprating inputs (September CPI, May-July earnings)
    - triple lock calculations for state pensions
    - earnings and September CPI uprating
    - economic assumption indices
    - Pension Credit threshold and protected Housing Benefit forecast indices
    - income tax and NICs threshold indexation after the freeze
    - Universal Credit standard allowance uprating (UC Act 2025 s. 1)
    - Universal Credit LCWRA element uprating (UC Act 2025 s. 3 freeze)
    - parameter uprating and backdating
    - conversion to fiscal year parameters

    Returns the tree and each parameter's timeline after projection (for gov
    parameters, just before the conversion to fiscal years), leaving out the
    ``baseline`` copy.

    ``parameters.baseline`` is the copy of the parameters without reforms
    that ``baseline_vat`` and the budget adjustments compare against, taken
    after the generated series are added and then uprated with the rest. A
    tree carrying dated reform changes passes ``unreformed``, the same tree
    without them, which the copy is taken from instead (#2188).
    ``annualise=False`` stops after the projection and adds no copy.
    ``generated`` holds the reform's changes to generated parameters, each
    written just after the step that generates it (see
    ``_add_generated_parameters``).
    ``enacted`` retains the YAML projection bases separately from runtime
    modifier edits. When omitted, the input tree supplies those bases, so
    an incomplete YAML rates update is still rejected.
    """
    validate_ni_scale_compatibility(parameters)
    parameters = _add_generated_parameters(parameters, generated, unreformed, enacted)

    # Create baseline parameters for reform comparisons
    if annualise:
        baseline = (
            parameters.clone()
            if unreformed is None
            else _add_generated_parameters(unreformed, enacted=enacted)
        )
        parameters.add_child("baseline", baseline)

    # Apply general parameter operations
    with canonical_ni_processing(parameters):
        propagate_parameter_metadata(parameters)
        with canonical_ni_uprating_references(parameters):
            uprate_parameters(parameters)
    parameters = backdate_parameters(parameters, BACKDATED_FROM)
    # Prior law's projected path for every parameter a reform can change: the
    # gov tree, before annualisation, and the trees outside it (household),
    # which are not annualised. ``baseline`` is a copy, whose parameters
    # keep the names of the ones it copies.
    projected = snapshot_timelines(parameters.gov)
    for key, child in parameters.children.items():
        if key not in ("gov", "baseline") and isinstance(child, ParameterNode):
            projected.update(snapshot_timelines(child))
    if not annualise:
        return parameters, projected
    parameters.gov = convert_to_fiscal_year_parameters(parameters.gov)
    return parameters, projected


class CountryTaxBenefitSystem(TaxBenefitSystem):
    """UK-specific tax and benefit system implementation.

    This class defines the UK tax-benefit system with all relevant
    variables, parameters, and entities (Person, BenUnit, Household).
    """

    basic_inputs: List[str] = [
        "brma",
        "local_authority",
        "region",
        "employment_income",
        "age",
    ]
    modelled_policies = COUNTRY_DIR / "programs.yaml"
    auto_carry_over_input_variables: bool = True

    variables: Dict[str, Variable]

    # Variables that hold part of another variable's value: each award's
    # claimant-or-partner part (CLAIMANT_OR_PARTNER_AWARDS). Neutralizing a
    # variable neutralizes its parts, so a value entered or set for a part
    # (as disable_simulated_benefits sets the claimant's and partner's awards
    # for each year) cannot outlive the award it is part of.
    variable_parts: Dict[str, Tuple[str, ...]] = {
        award: (part,) for award, part in CLAIMANT_OR_PARTNER_AWARDS.items()
    }

    def neutralize_variable(self, variable_name: str) -> None:
        super().neutralize_variable(variable_name)
        for part in self.variable_parts.get(variable_name, ()):
            super().neutralize_variable(part)

    def reset_parameter_caches(self):
        """Clear dated views through their Core owners, retaining the tree."""
        validate_ni_scale_compatibility(self.parameters)
        for node in [self.parameters, *canonical_descendants(self.parameters)]:
            if isinstance(node, ParameterNode):
                # The public operation clears this node and its ancestors;
                # root-only clearing would leave cached descendants behind.
                node.clear_parent_cache()
        _install_parameters(self, self.parameters)

    def reset_parameters(self) -> None:
        """Reset parameters by reloading from the parameters directory.

        The processed parameters it replaces are kept until
        ``process_parameters`` runs, so nodes a structural reform added to
        them survive the reload. Only a processed tree is kept, and a second
        reset before processing keeps the first one.
        """
        current = getattr(self, "parameters", None)
        if (
            getattr(self, "_parameters_before_reset", None) is None
            and current is not None
            and "baseline" in current.children
        ):
            self._parameters_before_reset = current
        self.load_parameters(self.parameters_dir)
        _install_parameters(self, add_removed_parameter_aliases(self.parameters))
        # Keep the YAML anchors before a simulation modifier can edit them.
        self._enacted_parameters = self.parameters.clone()

    def process_parameters(self) -> None:
        """Process and transform parameters with UK-specific adjustments.

        See ``process_parameter_tree``, which this runs on the system's
        parameters. ``projected_timelines`` keeps each parameter's
        timeline from before the conversion to fiscal years.

        The system's dated reform changes (``dated_assignments``) are written
        onto the parameters first, so a modifier that reloads and edits the
        parameters before processing them again (as ``no_economic_assumptions``
        does) keeps the reform. Nodes a structural reform added to the
        processed parameters before ``reset_parameters`` are added back (so
        a node a modifier deletes after the reset comes back too), and the
        legacy overrides of the annualised parameters are applied again.
        The parameters as they stood before the changes are kept as the base
        for later rebuilds. If processing fails, the system is left as it
        was.
        """
        previous = (self.parameters, self._projected_timelines, self._raw_parameters)
        before_reset = getattr(self, "_parameters_before_reset", None)
        self.reset_parameter_caches()
        try:
            # Processing changes the tree it is given, so it gets a copy: if
            # it fails, the system keeps the tree it had.
            self._rebuild(self.parameters.clone(), statutory=False)
            if before_reset is not None:
                graft_missing_nodes(before_reset, self.parameters)
            self._apply_legacy_overrides()
            add_capital_gains_projection(self.parameters, self.capital_gains_projection)
        except Exception:
            (
                self.parameters,
                self._projected_timelines,
                self._raw_parameters,
            ) = previous
            raise
        finally:
            self.reset_parameter_caches()
        self._parameters_before_reset = None

    def apply_parameter_assignments(
        self, assignments: List[ParameterAssignment]
    ) -> None:
        """Rebuild the parameters with more changes on the statutory timeline.

        Adds the changes to the system's ``dated_assignments`` and writes
        them all, in order, onto a fresh copy of the parameters the system
        was last processed from: the YAML as loaded, or that tree as a
        modifier left it before reprocessing. The parameters are then
        processed as current law is, so each change is uprated, indexed and
        annualised by its parameter's rule, and ``parameters.baseline`` stays
        without the changes. Where a change reaches the part of a parameter's
        timeline that projection fills, prior law there follows the path the
        parameter takes under the reform's other changes (see
        ``policyengine_uk.utils.dated_reforms``).

        A rebuild keeps the system's dated changes and legacy overrides, and
        the nodes a structural reform added to the processed parameters. It
        does not keep other edits made directly to existing processed
        parameters. If the rebuild fails, the system is left as it was.
        """
        if not assignments:
            return
        for assignment in assignments:
            check_capital_gains_projection_parameter(assignment.path)
        previous = (
            self.dated_assignments,
            self.parameters,
            self._projected_timelines,
            self._raw_parameters,
        )
        offset = len(self.dated_assignments)
        try:
            self.dated_assignments = self.dated_assignments + [
                replace(assignment, order=offset + index)
                for index, assignment in enumerate(
                    sorted(assignments, key=lambda assignment: assignment.order)
                )
            ]
            self.reset_parameter_caches()
            statutory = self._raw_parameters is None
            key = _assignments_key(self.dated_assignments) if statutory else None
            cached = _rebuilt_parameters_cache.get(key) if key is not None else None
            if cached is not None:
                _install_parameters(self, cached[0].clone())
                # Shared with the memo: read only through the copying
                # ``projected_timelines`` property.
                self._projected_timelines = cached[1]
            else:
                raw = (
                    statutory_parameters()
                    if statutory
                    else self._raw_parameters.clone()
                )
                self._rebuild(raw, statutory=statutory)
                if key is not None:
                    _remember_rebuilt(
                        key,
                        self.parameters.clone(),
                        copy_timelines(self._projected_timelines),
                    )
            graft_missing_nodes(previous[1], self.parameters)
            self._apply_legacy_overrides()
            add_capital_gains_projection(self.parameters, self.capital_gains_projection)
        except Exception:
            (
                self.dated_assignments,
                self.parameters,
                self._projected_timelines,
                self._raw_parameters,
            ) = previous
            raise
        finally:
            self.reset_parameter_caches()

    def parameters_with(self, assignments: List[ParameterAssignment]) -> ParameterNode:
        """The parameters this system would have with more dated changes.

        Rebuilds them on a shallow copy, which shares the variables and
        entities but holds its own copy of the parameters, so this system is
        left as it is, its parameter caches included, even when the rebuild
        fails. A rebuild only reassigns the copy's attributes. When this
        system was processed from the YAML and the changes' values can be
        memoised (plain numbers, booleans and strings), the memo then serves
        the same rebuild to this system if it is given the changes. The tree
        returned is never this system's own.
        """
        probe = copy.copy(self)
        _install_parameters(probe, self.parameters.clone())
        probe.apply_parameter_assignments(assignments)
        return probe.parameters

    def add_legacy_overrides(self, overrides: List[LegacyOverride]) -> None:
        """Apply changes to the annualised parameters and keep them.

        Kept so a later rebuild of the parameters applies them again, after
        the dated changes. If any override fails, none is applied or kept.
        """
        if not overrides:
            return
        for override in overrides:
            check_capital_gains_projection_parameter(override.path)
        # Every target is found before anything changes; ``update`` replaces
        # a parameter's ``values_list`` and marks it and its ancestors
        # modified, so keeping each list and those flags is enough to undo
        # the batch.
        targets = [self.parameters.get_child(override.path) for override in overrides]
        saved = [(target, target.values_list) for target in targets]
        flags = {}
        for target in targets:
            node = target
            while node is not None and id(node) not in flags:
                flags[id(node)] = (node, getattr(node, "modified", False))
                node = getattr(node, "parent", None)
        try:
            apply_legacy_overrides(self.parameters, overrides)
            add_capital_gains_projection(self.parameters, self.capital_gains_projection)
        except Exception:
            for target, values_list in saved:
                target.values_list = values_list
                target.parent.clear_parent_cache()
            for node, modified in flags.values():
                node.modified = modified
            raise
        finally:
            self.reset_parameter_caches()
        self.legacy_overrides = self.legacy_overrides + list(overrides)

    @property
    def projected_timelines(self) -> Dict[str, Timeline]:
        """Each parameter's projected timeline (gov: before annualisation).

        A copy: the timelines of an unreformed system, and of a rebuild
        taken from the memo, are shared with later systems.
        """
        return copy_timelines(
            self._projected_timelines
            if self._projected_timelines is not None
            else projected_timelines()
        )

    def _rebuild(self, raw: ParameterNode, statutory: bool) -> None:
        assignments = self.dated_assignments
        if not statutory:
            # The base later rebuilds start from: a modifier's edits to the
            # reloaded parameters are part of it.
            self._raw_parameters = raw.clone()
        if not assignments:
            parameters, self._projected_timelines = process_parameter_tree(
                raw, enacted=self._enacted_parameters
            )
            _install_parameters(self, parameters)
            return
        # Changes to parameters processing generates are written as each is
        # generated; the rest go on the statutory timeline first.
        defines = tree_defines(raw)
        on_timeline = [a for a in assignments if defines(a.path)]
        generated = [a for a in assignments if not defines(a.path)]
        generates = generated_parameter_defines()
        for assignment in generated:
            if not generates(assignment.path):
                # Not generated either: the error the lookup gives.
                raw.get_child(assignment.path)
        unreformed = raw.clone()
        projected = prior_law_projection(
            on_timeline, unreformed, statutory, generated, enacted=self._enacted_parameters
        )
        for assignment in on_timeline:
            write_assignment(raw.get_child(assignment.path), assignment, projected)
        parameters, self._projected_timelines = process_parameter_tree(
            raw, unreformed, generated=generated, enacted=self._enacted_parameters
        )
        _install_parameters(self, parameters)

    def _apply_legacy_overrides(self) -> None:
        if self.legacy_overrides:
            apply_legacy_overrides(self.parameters, self.legacy_overrides)

    def __init__(self, capital_gains_projection: CapitalGainsProjection | None = None):
        """Initialize the UK tax-benefit system with entities and parameters."""
        super().__init__(entities=[Person, BenUnit, Household])
        self.capital_gains_projection = capital_gains_projection

        # Load all variables from the variables directory
        self.add_variables_from_directory(COUNTRY_DIR / "variables")

        # Dated reform changes on the statutory timeline, and legacy
        # overrides of the annualised parameters, that every rebuild of the
        # parameters applies again. Replaced, never appended to in place, so a
        # cloned system does not share later additions.
        self.dated_assignments: List[ParameterAssignment] = []
        self.legacy_overrides: List[LegacyOverride] = []
        # The parameters this system was last processed from, when that is
        # not the YAML as loaded (None), and its own projected timelines,
        # when it has been processed itself (None: current law's).
        self._raw_parameters: Optional[ParameterNode] = None
        self._projected_timelines: Optional[Dict[str, Timeline]] = None
        # The processed parameters ``reset_parameters`` replaced, until
        # ``process_parameters`` adds back the nodes only they had.
        self._parameters_before_reset: Optional[ParameterNode] = None

        # Set up and process parameters
        self.parameters_dir = COUNTRY_DIR / "parameters"
        global _processed_parameters_cache, _statutory_parameters_cache
        global _projected_timelines_cache
        if _processed_parameters_cache is not None:
            self._enacted_parameters = _statutory_parameters_cache.clone()
            # Fast path: clone pre-processed parameters rather than re-running
            # the full pipeline (saves ~0.5s from convert_to_fiscal_year_parameters).
            # Reforms rebuild the parameters from the statutory tree through
            # apply_parameter_assignments, so they still get the full pipeline.
            _install_parameters(self, _processed_parameters_cache.clone())
        else:
            self.reset_parameters()
            _statutory_parameters_cache = self.parameters.clone()
            self._rebuild(self.parameters, statutory=True)
            self.reset_parameter_caches()
            _processed_parameters_cache = self.parameters.clone()
            # A copy: these timelines are prior law for every later reform,
            # and the lists just captured belong to this system's own tree.
            _projected_timelines_cache = copy_timelines(self._projected_timelines)
            self._projected_timelines = None

        # Derive CGT factors after fiscal conversion and outside the shared
        # current-law/rebuild caches, which are independent of this configuration.
        add_capital_gains_projection(self.parameters, self.capital_gains_projection)
        self.reset_parameter_caches()


def _ensure_caches() -> None:
    if _processed_parameters_cache is None:
        CountryTaxBenefitSystem()


def processed_parameters() -> ParameterNode:
    """The processed current-law parameters (shared: do not change them)."""
    _ensure_caches()
    return _processed_parameters_cache


def statutory_parameters() -> ParameterNode:
    """A fresh copy of the parameters as loaded from the YAML files."""
    _ensure_caches()
    return _statutory_parameters_cache.clone()


def statutory_parameter_defines() -> Callable[[str], bool]:
    """Whether the statutory parameter tree has a parameter at a path."""
    _ensure_caches()
    return tree_defines(_statutory_parameters_cache)


# The paths of the parameters the generation steps add to the statutory tree,
# other than the deprecated labour supply aliases.
_generated_paths_cache: Optional[frozenset] = None


def _leaf_paths(node: ParameterNode, prefix: str = "") -> List[str]:
    paths = []
    for key, child in node.children.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(child, LegacyNIParameter):
            continue
        if isinstance(child, Parameter):
            paths.append(path)
        elif isinstance(child, ParameterNode):
            paths += _leaf_paths(child, path)
        else:
            for index, bracket in enumerate(getattr(child, "brackets", [])):
                paths += _leaf_paths(bracket, f"{path}[{index}]")
    return paths


def generated_parameter_defines() -> Callable[[str], bool]:
    """Whether processing generates a parameter at a path.

    The deprecated labour supply aliases are left out: a change to one is a
    change to the parameter it copies (``canonicalize_lsr_parameter_path``).
    """
    global _generated_paths_cache
    if _generated_paths_cache is None:
        _ensure_caches()
        statutory = tree_defines(_statutory_parameters_cache)
        generated = _add_generated_parameters(statutory_parameters())
        _generated_paths_cache = frozenset(
            path
            for path in _leaf_paths(generated)
            if not statutory(path)
            and canonicalize_ni_parameter_path(canonicalize_lsr_parameter_path(path))
            == path
        )
    return _generated_paths_cache.__contains__


def reform_parameter_defines() -> Callable[[str], bool]:
    """Whether a reform's change to a path is written on the timeline.

    True for the parameters in the statutory tree and those processing
    generates; changes to any other path (one a structural reform adds) are
    legacy overrides of the annualised parameters.
    """
    statutory = statutory_parameter_defines()
    generated = generated_parameter_defines()
    return lambda path: statutory(path) or generated(path)


def parameter_reads_calendar_years() -> Callable[[str], bool]:
    """Whether a parameter's values are for calendar years.

    So a bare-year reform key names the calendar year, not the fiscal year
    (see ``policyengine_uk.utils.dated_reforms``). True for a parameter
    outside ``gov``, which is never annualised and is read at 1 January, and
    for one with ``calendar_year_series`` metadata on it or an ancestor node.
    """
    _ensure_caches()
    tree = _processed_parameters_cache

    def reads(path: str) -> bool:
        try:
            node = tree.get_child(path)
        except Exception:
            return False
        if path.split(".")[0] != "gov":
            return True
        while node is not None:
            if (getattr(node, "metadata", None) or {}).get(CALENDAR_YEAR_SERIES):
                return True
            node = getattr(node, "parent", None)
        return False

    return reads


def projected_timelines() -> Dict[str, Timeline]:
    """Current law's projected timeline for each parameter, by name.

    Shared: do not change them. ``CountryTaxBenefitSystem.projected_timelines``
    returns a copy.
    """
    _ensure_caches()
    return _projected_timelines_cache


def _same_timelines(a: Dict[str, Timeline], b: Dict[str, Timeline]) -> bool:
    def key(timeline):
        return [(entry.instant_str, entry.value) for entry in timeline or []]

    return a.keys() == b.keys() and all(key(a[name]) == key(b[name]) for name in a)


def prior_law_projection(
    assignments: List[ParameterAssignment],
    unreformed: ParameterNode,
    statutory: bool = True,
    generated: Optional[List[ParameterAssignment]] = None,
    enacted: Optional[ParameterNode] = None,
) -> Callable[[str], Optional[Timeline]]:
    """Prior law's projected timeline, by parameter name, for a reform.

    Where a change reaches the part of a parameter's timeline that
    projection fills (see ``requires_projection``), prior law there is the
    path that parameter takes with every other change in the reform but
    without its own. Each such parameter is projected with the others'
    changes, which are written with the previous pass's projections, until
    the projections stop changing. A chain of n such parameters, each
    projected from the one before, settles within n passes; projections
    that still change after that depend on each other in a cycle, which is
    an error. ``unreformed`` is the tree the changes are written onto;
    ``statutory`` says it is the YAML as loaded, whose projection without
    changes is cached. ``generated`` holds the reform's changes to generated
    parameters, which every pass makes too. ``enacted`` keeps the YAML bases
    separate from modifier edits through these intermediate projections too.
    """
    needing = sorted(
        {
            assignment.path
            for assignment in assignments
            if requires_projection(unreformed.get_child(assignment.path), assignment)
        }
    )
    if not needing:
        return lambda name: None
    start = (
        projected_timelines()
        if statutory and not generated
        else process_parameter_tree(
            unreformed.clone(),
            unreformed=unreformed,
            annualise=False,
            generated=generated,
            enacted=enacted,
        )[1]
    )
    environment = {path: start.get(path) for path in needing}

    def lookup(name: str) -> Optional[Timeline]:
        found = environment.get(name)
        return found if found is not None else start.get(name)

    for _ in range(len(needing) + 1):
        updated = {}
        for path in needing:
            tree = unreformed.clone()
            for assignment in assignments:
                if assignment.path != path:
                    write_assignment(
                        tree.get_child(assignment.path), assignment, lookup
                    )
            updated[path] = process_parameter_tree(
                tree, unreformed=unreformed, annualise=False, generated=generated,
                enacted=enacted,
            )[1].get(path)
        if _same_timelines(updated, environment):
            return lookup
        environment = updated
    raise ValueError(
        "Prior law's projected paths for "
        + ", ".join(needing)
        + " depend on each other in a cycle, so the reform cannot be applied."
    )


# Recently rebuilt parameters, by their dated changes, so simulations of the
# same reform (one per year or region, say) skip the rebuild. Entries are
# cloned on the way in and out and never changed.
_REBUILT_CACHE_SIZE = 4
_rebuilt_parameters_cache: "OrderedDict[tuple, Tuple[ParameterNode, Dict[str, Timeline]]]" = OrderedDict()


def _assignments_key(assignments: List[ParameterAssignment]) -> Optional[tuple]:
    """A memo key for the changes, or None when they cannot be memoised.

    Only plain numbers, booleans and strings are keyed, by type and value.
    Any other value (a list, or a number subclass whose repr could hide its
    value) is rebuilt every time.
    """
    key = []
    for a in assignments:
        if type(a.value) not in (int, float, bool, str):
            return None
        key.append((a.path, str(a.start), str(a.stop), type(a.value).__name__, a.value))
    return tuple(key)


def _remember_rebuilt(
    key: tuple, parameters: ParameterNode, projected: Dict[str, Timeline]
) -> None:
    _rebuilt_parameters_cache[key] = (parameters, projected)
    _rebuilt_parameters_cache.move_to_end(key)
    while len(_rebuilt_parameters_cache) > _REBUILT_CACHE_SIZE:
        _rebuilt_parameters_cache.popitem(last=False)


# Create system instance for module-level access
system = CountryTaxBenefitSystem()
parameters = system.parameters
variables = system.variables
