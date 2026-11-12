"""Reforms that policy YAML tests apply by dotted path (the `reforms` key)."""

from policyengine_core.reforms import Reform


class neutralise_income_support(Reform):
    """A reform that removes Income Support by neutralising income_support."""

    def apply(self):
        self.neutralize_variable("income_support")
