"""Refresh `schema/pve_api.json` from the Proxmox VE API schema.

The web interface's API viewer is driven by one file, `apidoc.js`, which
carries the whole API as JSON: every path, the methods it answers, the
parameters they take and the privileges they check. That is the only
machine-readable description Proxmox publishes, and it is what the
conformance test and the privilege map are built from.

Kept here are the facts a client needs - paths, methods, parameter names,
permission checks. The prose (descriptions, defaults, formats) is left
where it belongs, in the documentation the file comes from.

Run `python script/refresh_pve_api.py` after a Proxmox release and commit
what changes; the diff is then a readable list of what the API gained or
lost.

The extract carries a `_source` entry saying where it came from and when
the published file was last changed. `apidoc.js` itself names no version,
and the documentation site only lists past releases, so that timestamp is
the dependable answer to "is this still current": run the script, and it
says whether the published schema has moved since.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from urllib.request import urlopen

SOURCE = "https://pve.proxmox.com/pve-docs/api-viewer/apidoc.js"
TARGET = Path(__file__).parent.parent / "schema" / "pve_api.json"
# Where the extract records its own origin. Not a path, so everything
# reading the file skips the keys that do not start with "/".
SOURCE_KEY = "_source"


def fetch(url: str = SOURCE) -> tuple[list[dict[str, Any]], str]:
    """Return the schema out of `apidoc.js`, and when it was last published.

    The file wraps the whole API in one assignment, and the server's
    `Last-Modified` is the only version marker there is - the JavaScript
    carries none.
    """
    with urlopen(url) as response:
        text = response.read().decode("utf-8")
        last_modified = response.headers.get("Last-Modified", "")
    start = text.index("[")
    end = text.index("\n]\n;") + 2
    parsed: list[dict[str, Any]] = json.loads(text[start:end])
    return parsed, last_modified


def recorded_source() -> dict[str, str]:
    """Return the `_source` entry of the extract on disk, if it has one."""
    if not TARGET.exists():
        return {}
    on_disk: dict[str, Any] = json.loads(TARGET.read_text(encoding="utf-8"))
    source = on_disk.get(SOURCE_KEY)
    return source if isinstance(source, dict) else {}


def flatten(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return {path: {method: {parameters, check}}} for the whole tree."""
    routes: dict[str, dict[str, Any]] = {}
    for node in nodes:
        for method, info in (node.get("info") or {}).items():
            properties = (info.get("parameters") or {}).get("properties") or {}
            entry: dict[str, Any] = {"parameters": sorted(properties)}
            if check := (info.get("permissions") or {}).get("check"):
                entry["check"] = check
            routes.setdefault(node["path"], {})[method] = entry
        routes.update(flatten(node.get("children") or []))
    return routes


def main() -> None:
    """Write the trimmed schema and say what it holds."""
    before = recorded_source()
    nodes, last_modified = fetch()
    routes: dict[str, Any] = dict(flatten(nodes))
    routes[SOURCE_KEY] = {
        "url": SOURCE,
        "last_modified": last_modified,
        "fetched": datetime.now(UTC).date().isoformat(),
    }
    TARGET.parent.mkdir(exist_ok=True)
    TARGET.write_text(
        json.dumps(routes, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    paths = len(routes) - 1
    methods = sum(
        len(methods) for path, methods in routes.items() if path.startswith("/")
    )
    print(f"{TARGET}: {paths} paths, {methods} method and path pairs")
    if (was := before.get("last_modified")) and was != last_modified:
        print(f"published schema changed: {was} -> {last_modified}")
    elif was:
        print(f"published schema unchanged since {was}")


if __name__ == "__main__":
    main()
