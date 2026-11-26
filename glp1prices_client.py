"""Client for GLP1Prices.co's remote MCP server, the one place this plugin sends requests.

GLP1Prices.co publishes its daily US index of GLP-1 cash prices as a public, read-only MCP server:
no account and no API key. Each Dify tool here sends one JSON-RPC `tools/call` request to the fixed
address below and returns the answer. The address cannot be changed, redirects are not followed,
nothing is retried and nothing is stored.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

import requests

ENDPOINT = "https://glp1pricesco.founden.co/api/mcp"
USER_AGENT = "dify-plugin-glp1prices (+https://glp1pricesco.founden.co/developers)"
TIMEOUT = (5, 30)  # connect, read (seconds)
MAX_BYTES = 2 * 1024 * 1024
MAX_TEXT = 120


class Glp1PricesError(Exception):
    """GLP1Prices.co could not answer, or refused the request."""


@dataclass(frozen=True)
class Answer:
    text: str
    data: dict[str, Any] | None


def text_argument(parameters: Mapping[str, Any], name: str, required: bool = False) -> str | None:
    value = parameters.get(name)
    text = "" if value is None else str(value).strip()
    if not text:
        if required:
            raise Glp1PricesError(f"'{name}' is required.")
        return None
    if len(text) > MAX_TEXT:
        raise Glp1PricesError(f"'{name}' is too long (at most {MAX_TEXT} characters).")
    return text


def int_argument(parameters: Mapping[str, Any], name: str, low: int, high: int) -> int | None:
    value = parameters.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        raise Glp1PricesError(f"'{name}' must be a whole number.") from None
    return max(low, min(high, number))


def ask(tool: str, arguments: Mapping[str, Any]) -> Answer:
    """Call one tool of the GLP1Prices.co MCP server and return its text and structured answer."""
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": dict(arguments)}}
    try:
        response = requests.post(
            ENDPOINT,
            json=request,
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            allow_redirects=False,
            stream=True,
        )
    except requests.RequestException as exc:
        raise Glp1PricesError(f"GLP1Prices.co could not be reached ({type(exc).__name__}).") from None

    with response:
        if response.status_code != 200:
            raise Glp1PricesError(f"GLP1Prices.co answered HTTP {response.status_code}.")
        body = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            body.extend(chunk)
            if len(body) > MAX_BYTES:
                raise Glp1PricesError("GLP1Prices.co sent a larger answer than expected.")
        content_type = response.headers.get("Content-Type", "")

    message = _message(bytes(body), content_type)
    if "error" in message:
        error = message["error"]
        raise Glp1PricesError(f"GLP1Prices.co refused the request: {error.get('message') if isinstance(error, dict) else error}")
    result = message.get("result")
    if not isinstance(result, dict):
        raise Glp1PricesError("GLP1Prices.co sent an answer this plugin cannot read.")
    text = "\n".join(
        item["text"] for item in result.get("content") or [] if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str)
    ).strip()
    if result.get("isError"):
        raise Glp1PricesError(text or "GLP1Prices.co could not answer this request.")
    data = result.get("structuredContent")
    return Answer(text=text, data=data if isinstance(data, dict) else None)


def _message(body: bytes, content_type: str) -> dict[str, Any]:
    raw = body.decode("utf-8", errors="replace")
    try:
        if "text/event-stream" in content_type:
            events = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")]
            parsed = json.loads(events[-1]) if events else None
        else:
            parsed = json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        parsed = None
    if not isinstance(parsed, dict):
        raise Glp1PricesError("GLP1Prices.co sent an answer this plugin cannot read.")
    return parsed
