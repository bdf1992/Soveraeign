"""Small deterministic HTML primitives for the Human Binding surface."""

from __future__ import annotations

from typing import Any
import html


def e(value: Any) -> str:
    """Escape user/source-controlled values before they enter HTML."""
    return html.escape(str(value), quote=True)


def badge(label: str, tone: str = "muted") -> str:
    """One short uppercase tag. Tone is presentation; it asserts nothing."""
    return f'<span class="badge {e(tone)}">{e(label)}</span>'


def code(value: Any, css: str = "") -> str:
    """An escaped literal — an id, a digest, an authority string."""
    class_attr = f' class="{e(css)}"' if css else ""
    return f"<code{class_attr}>{e(value)}</code>"


def metric(value: Any, label: str, hint: str = "") -> str:
    """One headline figure with its label and an optional boundary hint."""
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
    """A navigator row. ``count`` of None renders no count at all.

    None is how a caller says the source behind this row was never read.
    Zero would claim it was read and reported nothing."""
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
    """A two-letter rail button. The title carries the full label."""
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
    """A titled block for the utility drawer, addressable by component."""
    eyebrow_html = f'<div class="eyebrow">{e(eyebrow)}</div>' if eyebrow else ""
    return (
        f'<section class="panel {e(css)}" data-component="{e(component)}">'
        f'{eyebrow_html}<h3>{e(title)}</h3>{body}</section>'
    )


def empty_state(title: str, detail: str, *, code_value: str = "") -> str:
    """Say why there is nothing here, and name the source that said so."""
    code_html = f"<p>{code(code_value)}</p>" if code_value else ""
    return (
        '<div class="empty-state" data-component="empty-state">'
        f'<strong>{e(title)}</strong><p>{e(detail)}</p>{code_html}</div>'
    )


def pill_button(label: str, *, filter_value: str = "", pressed: bool = False) -> str:
    """A filter pill. Setting the query changes visibility and nothing else."""
    return (
        f'<button class="pill{" active" if pressed else ""}" type="button" '
        f'data-filter="{e(filter_value)}">{e(label)}</button>'
    )
