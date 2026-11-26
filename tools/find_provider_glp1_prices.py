"""Find one provider's GLP-1 prices: every current tirzepatide and semaglutide price of one US provider."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from glp1prices_client import ask, text_argument


class FindProviderGlp1PricesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        answer = ask("find_seller_glp1_prices", {"seller": text_argument(tool_parameters, "provider", required=True)})
        yield self.create_text_message(answer.text)
        if answer.data is not None:
            yield self.create_json_message(answer.data)
