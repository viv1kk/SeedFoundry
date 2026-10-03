"""Structural validity of a dashboard payload against its descriptor (T-08, FR-T-2).

The data-swap test runs the same descriptor and query engine on a second, different estate and
asks two things: is each payload structurally valid (every panel the descriptor names has data
of the shape its mark needs, consistent within itself), and is the structure the same on both
estates. Values may differ; structure may not. Numbers are T-16's business, not this check's.
"""

from __future__ import annotations

from typing import Any

from seedfoundry.data.model import Dataset

KPI_KEYS = {"value"}


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def problems(descriptor: dict[str, Any], payload: dict[str, Any], data: Dataset) -> list[str]:
    """Every structural problem; none for a valid payload."""
    found: list[str] = []
    panels = payload.get("panels", {})
    class_ids = [c["id"] for c in descriptor["classes"]]
    if payload.get("dashboard") != descriptor["id"]:
        found.append(f"payload is for {payload.get('dashboard')!r}, not {descriptor['id']!r}")
    crumbs = payload.get("drill", {}).get("crumbs", [])
    if not crumbs or crumbs[0].get("path") != "":
        found.append("drill: no root crumb")
    missing = [p["id"] for p in descriptor["panels"] if p["id"] not in panels]
    extra = [pid for pid in panels if pid not in {p["id"] for p in descriptor["panels"]}]
    found += [f"{pid}: no data" for pid in missing] + [f"{pid}: data for a panel the descriptor does not have" for pid in extra]

    for panel in descriptor["panels"]:
        pid, mark = panel["id"], panel["mark"]
        body = panels.get(pid)
        if body is None:
            continue
        if mark == "kpi":
            if not _is_count(body.get("value")):
                found.append(f"{pid}: value is not a count")
        elif mark == "treemap":
            def walk(nodes: list[dict[str, Any]], depth: int) -> None:
                for node in nodes:
                    if not {"id", "name", "level", "value"} <= node.keys() or not _is_count(node["value"]) or node["value"] == 0:
                        found.append(f"{pid}: a node without id, name, level and a positive size")
                    if node.get("level") == "class" and node.get("class") not in class_ids:
                        found.append(f"{pid}: a leaf with no class")
                    if node.get("children"):
                        walk(node["children"], depth + 1)
            walk(body.get("nodes", []), 0)
            if [item.get("class") for item in body.get("legend", [])] != class_ids:
                found.append(f"{pid}: legend does not list the classes in order")
        elif mark in ("bar", "line", "pie"):
            # A pie keeps the bar's data shape (one value per category), so T-08 reads it alike.
            categories = body.get("months") if mark == "line" else body.get("categories")
            if not isinstance(categories, list):
                found.append(f"{pid}: no categories")
                continue
            if mark == "line" and categories != list(data.months):
                found.append(f"{pid}: months are not the dataset's {len(data.months)} months")
            series_ids = [s["id"] for s in panel["series"]]
            series = body.get("series") if "series" in body else {series_ids[0]: body.get("values")}
            for sid in series_ids:
                values = (series or {}).get(sid)
                if not isinstance(values, list) or len(values) != len(categories):
                    found.append(f"{pid}: series {sid} does not have one value per category")
                elif not all(v is None or _is_count(v) for v in values):
                    found.append(f"{pid}: series {sid} has a value that is not a count")
            if "withheld" in panel:
                flags = body.get("withheld", [])
                values = body.get("values", [])
                if len(flags) != len(categories) or any(flag != (value is None) for flag, value in zip(flags, values, strict=False)):
                    found.append(f"{pid}: withheld flags do not match the missing values")
        elif mark == "table":
            rows = body.get("rows")
            if not isinstance(rows, list):
                found.append(f"{pid}: no rows")
                continue
            columns = [c["id"] for c in panel["columns"]]
            if any(not set(columns) <= row.keys() for row in rows):
                found.append(f"{pid}: a row without every column")
            if panel.get("total_row") and not set(columns) <= body.get("total", {}).keys():
                found.append(f"{pid}: no total row with every column")
            if panel.get("page_size"):
                if len(rows) > panel["page_size"]:
                    found.append(f"{pid}: more rows than a page")
                if not all(_is_count(body.get(k)) for k in ("page", "pages", "total")):
                    found.append(f"{pid}: no page, pages and total")
            if panel.get("footer") == "class_counts" and set(body.get("footer", {})) != {*class_ids, "total"}:
                found.append(f"{pid}: footer is not the class counts and the total")
        else:
            found.append(f"{pid}: unknown mark {mark}")
    return found


def shape(value: Any, path: str = "") -> frozenset[str]:
    """The payload's structure: every key path, list items merged ("[]"), values ignored. Two
    payloads built by the same logic from different data have the same shape."""
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, inner in value.items():
            here = f"{path}.{key}"
            paths.add(here)
            paths |= shape(inner, here)
    elif isinstance(value, list):
        for item in value:
            paths |= shape(item, f"{path}[]")
    return frozenset(paths)
