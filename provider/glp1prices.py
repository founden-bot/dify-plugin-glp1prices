from typing import Any

from dify_plugin import ToolProvider


class Glp1PricesProvider(ToolProvider):
    """GLP1Prices.co's index is public and keyless: there are no credentials to check."""

    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        return None
