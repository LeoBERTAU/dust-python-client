# dust_client/utils.py

from __future__ import annotations

import json
from typing import Iterator, Dict, Any

import httpx

from .exceptions import DustError


def stream_sse_json(
    http: httpx.Client,
    *,
    method: str,
    path: str,
    timeout: float,
    error_cls=DustError,
) -> Iterator[Dict[str, Any]]:
    """
    Unified streaming parser for Dust SSE/NDJSON endpoints.

    This supports:
      - Server-Sent Events (lines beginning with "data: {...}")
      - NDJSON (one JSON per line)

    It yields each parsed JSON object (dict).

    Args:
        http: The underlying httpx.Client
        method: HTTP method ("GET", usually)
        path: Full path (relative to client's base_url)
        timeout: Streaming timeout
        error_cls: Exception class to raise on protocol/network errors

    Yields:
        dict events as they arrive.
    """

    try:
        with http.stream(
            method,
            path,
            headers={"Accept": "text/event-stream"},
            timeout=timeout,
        ) as resp:

            if resp.status_code != 200:
                # Try reading body for diagnostics
                try:
                    body = resp.read().decode("utf-8", errors="replace")
                except Exception:
                    body = None
                raise error_cls(
                    f"Streaming error: status={resp.status_code}, body={body!r}"
                )

            buffer = ""

            for chunk in resp.iter_text():
                buffer += chunk

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line or line.startswith(":"):
                        continue

                    # SSE style: "data: {...}"
                    if line.startswith("data:"):
                        data_str = line[len("data:"):].strip()
                    else:
                        # NDJSON style — whole line is JSON
                        data_str = line

                    if not data_str:
                        continue

                    try:
                        obj = json.loads(data_str)
                    except json.JSONDecodeError:
                        # malformed chunk — ignore
                        continue

                    if isinstance(obj, dict):
                        yield obj

    except Exception as exc:
        if isinstance(exc, error_cls):
            raise
        raise error_cls(f"Streaming failure: {exc}") from exc