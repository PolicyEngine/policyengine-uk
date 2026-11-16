"""Single-source NI scale leaves with legacy scalar read/update compatibility.

Views are discoverable Parameters for existing metadata serializers. Numerical
processing explicitly excludes them; no view owns a second policy timeline.
Retire the Core-internal adaptations when stable alias/processing contracts
replace them. Remove legacy views through an explicit compatibility migration
once callers, saved reforms and metadata consumers use canonical scale paths;
retain their contract tests until that transition is complete.
"""

import copy
from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType

from policyengine_core.commons import empty_clone
from policyengine_core.parameters import Parameter, ParameterNode, ParameterScale

NI_PREFIX = "gov.hmrc.national_insurance."
NI_LEGACY_PATHS = MappingProxyType(
    {
        NI_PREFIX + old: NI_PREFIX + new
        for old, new in {
            "class_1.rates.employee.main": "class_1.employee_scale[1].rate",
            "class_1.rates.employee.additional": "class_1.employee_scale[2].rate",
            "class_1.thresholds.primary_threshold": "class_1.employee_scale[1].threshold",
            "class_1.thresholds.upper_earnings_limit": "class_1.employee_scale[2].threshold",
            "class_1.rates.employer": "class_1.employer_scale[1].rate",
            "class_1.thresholds.secondary_threshold": "class_1.employer_scale[1].threshold",
            "class_4.rates.main": "class_4.contribution_scale[1].rate",
            "class_4.rates.additional": "class_4.contribution_scale[2].rate",
            "class_4.thresholds.lower_profits_limit": "class_4.contribution_scale[1].threshold",
            "class_4.thresholds.upper_profits_limit": "class_4.contribution_scale[2].threshold",
        }.items()
    }
)


def canonicalize_ni_parameter_path(path):
    prefix = ""
    while path.startswith("baseline."):
        prefix += "baseline."
        path = path[len("baseline.") :]
    return prefix + NI_LEGACY_PATHS.get(path, path)


@dataclass(frozen=True)
class NIComponent:
    """Original bracket identity, even when custom thresholds coincide/cross."""

    threshold: object
    rate: object


def _validate_ni_zero_bracket(scale):
    """The initial zero band is a fixed representation sentinel."""
    bracket = scale.brackets[0]
    for name in ("threshold", "rate"):
        leaf = bracket.children.get(name)
        if (
            not isinstance(leaf, Parameter)
            or not leaf.values_list
            or any(point.value != 0 for point in leaf.values_list)
        ):
            raise ValueError(
                f"NI canonical leaf {scale.name}[0].{name} is fixed at zero; "
                "update the contribution bands after bracket 0 instead"
            )


class NIParameterScale(ParameterScale):
    def _get_at_instant(self, instant):
        _validate_ni_zero_bracket(self)
        scale = super()._get_at_instant(instant)
        scale.components = tuple(
            NIComponent(bracket.threshold(instant), bracket.rate(instant))
            for bracket in self.brackets
        )
        return scale


class LegacyNIParameter(Parameter):
    """A named scalar descriptor whose values belong to a canonical NI leaf."""

    def __init__(self, name, target_path):
        self.name = name
        self.target_path = target_path
        self.parent = None
        self._at_instant_cache = {}

    @property
    def target(self):
        node = self.parent
        while node is not None and not getattr(node, "_ni_scale_anchor", False):
            node = getattr(node, "parent", None)
        if node is None:
            raise ValueError(
                f"Detached NI compatibility view {self.name} has no policy tree"
            )
        return node.get_child(self.target_path)

    @property
    def values_list(self):
        return self.target.values_list

    @values_list.setter
    def values_list(self, value):
        target = self.target
        target.values_list = value
        target.clear_parent_cache()
        target.mark_as_modified()

    @property
    def metadata(self):
        return self.target.metadata

    @metadata.setter
    def metadata(self, value):
        self.target.metadata = value

    @property
    def description(self):
        return self.target.description

    @description.setter
    def description(self, value):
        self.target.description = value

    @property
    def documentation(self):
        return getattr(self.target, "documentation", None)

    @property
    def file_path(self):
        return self.target.file_path

    def update(self, *args, **kwargs):
        return self.target.update(*args, **kwargs)

    def _get_at_instant(self, instant):
        return self.target.get_at_instant(instant)

    def clear_parent_cache(self):
        self.target.clear_parent_cache()

    def mark_as_modified(self):
        self.target.mark_as_modified()

    def clone(self):
        # A standalone leaf clone is an independent ordinary Parameter, as it
        # was before migration. Parent cloning recreates descriptors instead.
        leaf = self.target.clone()
        leaf.name = self.name
        owner = ParameterNode("", data={})
        owner.add_child("leaf", leaf)
        return leaf


class LegacyNIDiscoveryParameter(LegacyNIParameter):
    """Presentation-only alias; direct lookup keeps canonical metadata identity."""

    @property
    def metadata(self):
        return {**self.target.metadata, "household": False, "economy": False}


class NICompatibilityNode(ParameterNode):
    def get_descendants(self):
        # Enumerators such as the API expose both stable public IDs, but only
        # the canonical leaf is an editable discovery control. The registered
        # child itself is unchanged for get_parameter/manual-child updates.
        for child in self.children.values():
            if isinstance(child, LegacyNIParameter):
                view = LegacyNIDiscoveryParameter(child.name, child.target_path)
                view.parent = child.parent
                yield view
            else:
                yield child
            yield from child.get_descendants()

    def clone(self):
        clone = empty_clone(self)
        clone.__dict__ = self.__dict__.copy()
        clone.metadata = copy.deepcopy(self.metadata)
        clone.children = {
            key: LegacyNIParameter(child.name, child.target_path)
            if isinstance(child, LegacyNIParameter)
            else child.clone()
            for key, child in self.children.items()
        }
        for key, child in clone.children.items():
            setattr(clone, key, child)
            child.parent = clone
        clone._at_instant_cache = {}
        return clone

    def _get_at_instant(self, instant):
        # A sibling canonical update clears the root's cache, not a legacy
        # sibling's cache. Rebuild this cheap numeric view on every lookup.
        self._at_instant_cache.pop(instant, None)
        return super()._get_at_instant(instant)


class _CanonicalChildren(dict):
    """Explicit processing iteration, retaining legacy key lookups."""

    def items(self):
        return (
            (key, value)
            for key, value in super().items()
            if not isinstance(value, LegacyNIParameter)
        )

    def values(self):
        return (value for _, value in self.items())

    def __iter__(self):
        return (key for key, _ in self.items())


def canonical_descendants(node):
    return (
        child
        for child in node.get_descendants()
        if not isinstance(child, LegacyNIParameter)
    )


@contextmanager
def canonical_ni_processing(parameters):
    """Only on an owned processing tree; restore discovery even on errors.

    The real root/leaves and their parents retain identity. Core's nested
    traversal and its independent child/path walker see canonical leaves;
    explicit legacy lookup still resolves the view. No global/caller mode.
    """
    saved = []
    try:
        for node in list(parameters.get_descendants()):
            if isinstance(node, ParameterNode) and any(
                isinstance(child, LegacyNIParameter) for child in node.children.values()
            ):
                saved.append((node, node.children))
                node.children = _CanonicalChildren(node.children)
        yield parameters
    finally:
        for node, children in reversed(saved):
            node.children = children


@contextmanager
def canonical_ni_uprating_references(parameters):
    """Map NI dependency names for Core's canonical-leaf ordering only."""
    saved = []
    try:
        for leaf in canonical_descendants(parameters):
            if not isinstance(leaf, Parameter):
                continue
            value = leaf.metadata.get("uprating")
            path = (
                value
                if isinstance(value, str)
                else (value.get("parameter") if isinstance(value, dict) else None)
            )
            if path is None:
                continue
            canonical = canonicalize_ni_parameter_path(path)
            if canonical != path:
                saved.append((leaf.metadata, value))
                leaf.metadata["uprating"] = (
                    canonical
                    if isinstance(value, str)
                    else {
                        **value,
                        "parameter": canonical,
                    }
                )
        yield parameters
    finally:
        for metadata, value in reversed(saved):
            metadata["uprating"] = value


def add_ni_scale_compatibility(parameters):
    """Install relative, clone-safe views without copied scalar histories."""
    # Baseline copies use their own NI anchor and canonical components.
    roots = [parameters]
    if "baseline" in parameters.children:
        roots.append(parameters.children["baseline"])
    for root in roots:
        ni = root.gov.hmrc.national_insurance
        for name in (
            "class_1.employee_scale",
            "class_1.employer_scale",
            "class_4.contribution_scale",
        ):
            scale = ni.get_child(name)
            scale.__class__ = NIParameterScale
        ni._ni_scale_anchor = True
        for old, new in NI_LEGACY_PATHS.items():
            parts = old[len(NI_PREFIX) :].split(".")
            node = ni
            for part in parts[:-1]:
                node.__class__ = NICompatibilityNode
                if part not in node.children:
                    node.add_child(
                        part, NICompatibilityNode(node.name + "." + part, data={})
                    )
                node = node.children[part]
                if not isinstance(node, ParameterNode):
                    raise ValueError(
                        f"NI legacy subtree {old} was structurally replaced; use {new}"
                    )
            node.__class__ = NICompatibilityNode
            previous = node.children.get(parts[-1])
            if previous is not None and not isinstance(previous, LegacyNIParameter):
                raise ValueError(
                    f"NI legacy leaf {old} was structurally replaced; update {new}"
                )
            if previous is None:
                node.add_child(parts[-1], LegacyNIParameter(old, new[len(NI_PREFIX) :]))
    return parameters


def validate_ni_scale_compatibility(parameters):
    """Reject conflicting subtree replacement before numerical processing.

    Leaf updates and unrelated added nodes are supported. Replacing either
    spelling's structure is not silently interpreted as a second schedule.
    """
    roots = [parameters]
    if "baseline" in parameters.children:
        roots.append(parameters.children["baseline"])
    for root in roots:
        try:
            ni = root.gov.hmrc.national_insurance
        except (AttributeError, ValueError) as error:
            raise ValueError(
                "NI canonical subtree was structurally replaced; retain the schedules and update component leaves"
            ) from error
        for path, count in (
            ("class_1.employee_scale", 3),
            ("class_1.employer_scale", 2),
            ("class_4.contribution_scale", 3),
        ):
            try:
                scale = ni.get_child(path)
            except (KeyError, AttributeError, ValueError) as error:
                raise ValueError(
                    f"NI canonical schedule {path} was structurally replaced; update its component leaves"
                ) from error
            if not isinstance(scale, NIParameterScale) or len(scale.brackets) != count:
                raise ValueError(
                    f"NI canonical schedule {path} was structurally replaced; update its component leaves"
                )
            _validate_ni_zero_bracket(scale)
        for old, new in NI_LEGACY_PATHS.items():
            node = ni
            try:
                for part in old[len(NI_PREFIX) :].split("."):
                    node = node.children[part]
            except (KeyError, AttributeError, ValueError) as error:
                raise ValueError(
                    f"NI legacy path {old} was structurally replaced; update {new}"
                ) from error
            try:
                valid = isinstance(
                    node, LegacyNIParameter
                ) and node.target is root.get_child(new)
            except (KeyError, AttributeError, ValueError) as error:
                raise ValueError(
                    f"NI canonical leaf {new} was structurally replaced; update its value"
                ) from error
            if not valid:
                raise ValueError(
                    f"NI legacy path {old} was structurally replaced; update {new}"
                )
