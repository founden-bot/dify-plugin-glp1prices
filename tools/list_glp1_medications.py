"""List GLP-1 medications: the price lists the GLP1Prices.co index keeps today."""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from glp1prices_client import ask


class ListGlp1MedicationsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        answer = ask("list_glp1_medications", {})
        yield self.create_text_message(answer.text)
        if answer.data is not None:
            yield self.create_json_message(answer.data)
