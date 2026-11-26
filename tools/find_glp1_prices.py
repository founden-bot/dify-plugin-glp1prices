"""Find GLP-1 prices: the lowest current US cash prices of one medicine or brand."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from glp1prices_client import ask, int_argument, text_argument


class FindGlp1PricesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        arguments: dict[str, Any] = {"medication": text_argument(tool_parameters, "medication", required=True)}
        limit = int_argument(tool_parameters, "limit", 1, 25)
        if limit is not None:
            arguments["limit"] = limit
        answer = ask("find_glp1_prices", arguments)
        yield self.create_text_message(answer.text)
        if answer.data is not None:
            yield self.create_json_message(answer.data)
