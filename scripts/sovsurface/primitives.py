"""Small deterministic HTML primitives for the Human Binding surface."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any
import html


def e(value: Any) -> str:
    """Escape user/source-controlled values before they enter HTML."""
    return html.escape(str(value), quote=True)


def attrs(values: Mapping[str, Any] | None = None) -> str:
    """Render a stable attribute mapping, omitting None and false booleans."""
    if not values:
        return ""
    parts: list[str] = []
    for key in sorted(values):
        value = values[key]
        if value is None or value is False:
            continue
        safe_key = key.replace("_", "-")
        if value is True:
            parts.append(safe_key)
        else:
            parts.append(f'{safe_key}="{e(value)}"')
    return (" " + " ".join(parts)) if parts else ""


def badge(label: str, tone: str = "muted") -> str:
    return f'<span class="badge {e(tone)}">{e(label)}</span>'


def code(value: Any, css: str = "") -> str:
    class_attr = f' class="{e(css)}"' if css else ""
    return f"<code{class_attr}>{e(value)}</code>"


def metric(value: Any, label: str, hint: str = "") -> str:
    hint_html = f'<small>{e(hint)}</small>' if hint else ""
    return (
        '<div class="metric" data-component="metric">'
        f'<b>{e(value)}</b><span>{e(label)}</span>{hint_html}</div>'
    )


def nav_item(
    label: str,
    *,
    icon: str = "#",
    active: bool = False,
    count: int | None = None,
    filter_value: str | None = None,
) -> str:
    count_html = f'<span class="count">{count}</span>' if count is not None else ""
    return (
        f'<button class="nav-item{" active" if active else ""}" '
        f'data-filter="{e(filter_value or "")}" type="button">'
        f'<span class="nav-icon">{e(icon)}</span><span>{e(label)}</span>{count_html}</button>'
    )


def rail_item(
    label: str,
    *,
    short: str,
    filter_value: str = "",
    active: bool = False,
) -> str:
    return (
        f'<button class="rail-item{" active" if active else ""}" '
        f'title="{e(label)}" data-filter="{e(filter_value)}" type="button">'
        f'{e(short[:2].upper())}</button>'
    )


def panel(
    title: str,
    body: str,
    *,
    eyebrow: str = "",
    css: str = "",
    component: str = "panel",
) -> str:
    eyebrow_html = f'<div class="eyebrow">{e(eyebrow)}</div>' if eyebrow else ""
    return (
        f'<section class="panel {e(css)}" data-component="{e(component)}">'
        f'{eyebrow_html}<h3>{e(title)}</h3>{body}</section>'
    )


def definition_rows(rows: Iterable[tuple[str, str]]) -> str:
    body = "".join(f"<dt>{e(label)}</dt><dd>{value}</dd>" for label, value in rows)
    return f'<dl class="facts">{body}</dl>'


def empty_state(title: str, detail: str, *, code_value: str = "") -> str:
    code_html = f"<p>{code(code_value)}</p>" if code_value else ""
    return (
        '<div class="empty-state" data-component="empty-state">'
        f'<strong>{e(title)}</strong><p>{e(detail)}</p>{code_html}</div>'
    )


def pill_button(label: str, *, filter_value: str = "", pressed: bool = False) -> str:
    return (
        f'<button class="pill{" active" if pressed else ""}" type="button" '
        f'data-filter="{e(filter_value)}">{e(label)}</button>'
    )
