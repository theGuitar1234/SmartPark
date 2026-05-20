from __future__ import annotations

import flet as ft


class C:
    ink = "#102033"
    muted = "#667085"
    soft = "#F5F8FC"
    panel = "#FFFFFF"
    line = "#E5EAF1"
    blue = "#2563EB"
    blue_dark = "#1D4ED8"
    blue_soft = "#EAF2FF"
    green = "#15803D"
    green_soft = "#EAF8EF"
    red = "#B42318"
    red_soft = "#FDECEC"
    amber = "#B54708"
    amber_soft = "#FFF4E5"
    slate = "#475467"
    slate_soft = "#EEF2F6"
    purple = "#6D28D9"
    purple_soft = "#F1EAFE"


STATUS_COLORS = {
    "Available": (C.green, C.green_soft),
    "Occupied": (C.red, C.red_soft),
    "Reserved": (C.amber, C.amber_soft),
    "Maintenance": (C.slate, C.slate_soft),
    "Disabled": ("#344054", "#EAECF0"),
    "Active": (C.blue, C.blue_soft),
    "Completed": (C.green, C.green_soft),
    "Cancelled": (C.slate, C.slate_soft),
    "Paid": (C.green, C.green_soft),
    "Unpaid": (C.red, C.red_soft),
    "Pending": (C.amber, C.amber_soft),
    "Failed": (C.red, C.red_soft),
    "Refunded": (C.purple, C.purple_soft),
    "Clear": (C.green, C.green_soft),
    "Fault": (C.red, C.red_soft),
    "Unknown": (C.slate, C.slate_soft),
}


SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}
RADIUS = {"sm": 8, "md": 12, "lg": 18, "xl": 24}


def shadow(level: int = 1):
    opacity = 0.07 if level == 1 else 0.12
    blur = 18 if level == 1 else 28
    return ft.BoxShadow(blur_radius=blur, color=ft.Colors.with_opacity(opacity, ft.Colors.BLACK), offset=ft.Offset(0, 8))


def badge(text: str):
    fg, bg = STATUS_COLORS.get(str(text), (C.slate, C.slate_soft))
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=99,
        bgcolor=bg,
        content=ft.Text(str(text), size=11, weight=ft.FontWeight.W_700, color=fg),
    )


def section_title(title: str, subtitle: str = ""):
    items = [ft.Text(title, size=18, weight=ft.FontWeight.W_800, color=C.ink)]
    if subtitle:
        items.append(ft.Text(subtitle, size=12, color=C.muted))
    return ft.Column(items, spacing=1)


def panel(content: ft.Control, padding: int = 18, expand: bool | int | None = None, width: int | None = None, height: int | None = None):
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=C.panel,
        border=ft.border.all(1, C.line),
        border_radius=RADIUS["lg"],
        shadow=shadow(1),
        expand=expand,
        width=width,
        height=height,
    )


def text_input(label: str, value: str = "", width: int | None = None, password: bool = False, helper: str = "", multiline: bool = False):
    return ft.TextField(
        label=label,
        value=value,
        width=width,
        password=password,
        can_reveal_password=password,
        dense=True,
        multiline=multiline,
        min_lines=2 if multiline else None,
        max_lines=4 if multiline else None,
        border_radius=RADIUS["md"],
        border_color=C.line,
        focused_border_color=C.blue,
        helper_text=helper or None,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=12),
    )


def select_input(label: str, options: list[str], value: str | None = None, width: int | None = None, helper: str = ""):
    return ft.Dropdown(
        label=label,
        value=value if value is not None else (options[0] if options else None),
        options=[ft.dropdown.Option(option) for option in options],
        width=width,
        dense=True,
        border_radius=RADIUS["md"],
        border_color=C.line,
        focused_border_color=C.blue,
        helper_text=helper or None,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
    )


def primary_button(text: str, icon=None, on_click=None, width=None):
    return ft.ElevatedButton(
        text,
        icon=icon,
        on_click=on_click,
        width=width,
        height=42,
        style=ft.ButtonStyle(
            bgcolor=C.blue,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        ),
    )


def secondary_button(text: str, icon=None, on_click=None, width=None):
    return ft.OutlinedButton(
        text,
        icon=icon,
        on_click=on_click,
        width=width,
        height=42,
        style=ft.ButtonStyle(
            color=C.ink,
            side=ft.BorderSide(1, C.line),
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        ),
    )


def danger_button(text: str, icon=None, on_click=None, width=None):
    return ft.ElevatedButton(
        text,
        icon=icon,
        on_click=on_click,
        width=width,
        height=42,
        style=ft.ButtonStyle(
            bgcolor=C.red,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        ),
    )
