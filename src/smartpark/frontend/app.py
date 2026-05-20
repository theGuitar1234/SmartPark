from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import flet as ft

from .api_client import ApiError, SmartParkClient
from .design import C, STATUS_COLORS, badge, danger_button, panel, primary_button, secondary_button, section_title, select_input, text_input
from .state import AppState

SLOT_TYPES = ["Standard", "Motorcycle", "EV", "Disabled Access", "Truck", "VIP"]
VEHICLE_TYPES = ["Car", "Motorcycle", "EV", "Disabled Access", "Truck", "VIP"]
SLOT_STATUSES = ["Available", "Occupied", "Reserved", "Maintenance", "Disabled"]
SESSION_STATUSES = ["All", "Active", "Completed", "Cancelled"]
PAYMENT_STATUSES = ["All", "Unpaid", "Pending", "Paid", "Failed", "Refunded"]
PAYMENT_METHODS = ["Cash", "Card", "Online", "Wallet"]
SENSOR_STATES = ["Clear", "Occupied", "Fault", "Unknown"]


def safe_items(data: dict | None) -> list[dict]:
    return data.get("items", []) if isinstance(data, dict) else []


def money(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


def percent(value: Any) -> str:
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "0.0%"


def compact_time(value: Any) -> str:
    if not value:
        return ""
    text = str(value).replace("T", " ").replace("Z", "")
    return text[:16]


def main(page: ft.Page):
    state = AppState(client=SmartParkClient())
    page.title = "SmartPark"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = C.soft
    page.padding = 0
    page.window.width = 1440
    page.window.height = 900
    page.window.min_width = 1100
    page.window.min_height = 720

    root = ft.Container(expand=True)

    nav_items = [
        ("Dashboard", ft.Icons.DASHBOARD_OUTLINED),
        ("Zone Management", ft.Icons.MAP_OUTLINED),
        ("Sessions & Payments", ft.Icons.TIMER_OUTLINED),
        ("Forms Library", ft.Icons.FACT_CHECK),
        ("System Configuration", ft.Icons.SETTINGS),
        ("Reports", ft.Icons.ASSESSMENT_OUTLINED),
    ]

    def notify(message: str, error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=C.red if error else C.green,
            show_close_icon=True,
        )
        page.open(snack)
        page.update()

    def refresh():
        page.controls.clear()
        if not state.user:
            render_login()
        else:
            root.content = shell()
            guard_tree(root)
            page.add(root)
            page.update()

    def switch_view(name: str):
        state.view = name
        refresh()

    def clean_error_message(ex: Exception) -> str:
        message = str(ex).strip()
        if not message:
            message = ex.__class__.__name__
        return message

    def handle_api_error(ex: Exception):
        notify(clean_error_message(ex), True)

    def guard_event(handler: Callable | None):
        if handler is None or getattr(handler, "_smartpark_guarded", False):
            return handler

        def guarded(event=None):
            try:
                return handler(event)
            except Exception as ex:
                handle_api_error(ex)
                return False

        setattr(guarded, "_smartpark_guarded", True)
        return guarded

    def guard_tree(control):
        if control is None:
            return
        for attr in ("on_click", "on_change", "on_submit"):
            if hasattr(control, attr):
                handler = getattr(control, attr, None)
                if handler is not None:
                    setattr(control, attr, guard_event(handler))
        for attr in ("controls", "actions"):
            children = getattr(control, attr, None)
            if children:
                for child in list(children):
                    guard_tree(child)
        for attr in ("content", "leading", "trailing", "title", "subtitle"):
            child = getattr(control, attr, None)
            if child is not None:
                guard_tree(child)

    def open_dialog(title: str, controls: list[ft.Control], on_save: Callable | None = None, save_text: str = "Save", width: int = 560, destructive: bool = False):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.W_800, color=C.ink),
            content=ft.Container(width=width, content=ft.Column(controls, tight=True, spacing=14, scroll=ft.ScrollMode.AUTO)),
        )

        def close(_):
            dialog.open = False
            page.update()

        actions = [ft.TextButton("Cancel", on_click=close, style=ft.ButtonStyle(color=C.muted))]
        if on_save:
            def save(e):
                try:
                    result = on_save(e)
                    if result is not False:
                        dialog.open = False
                        page.update()
                except Exception as ex:
                    notify(str(ex), True)
            actions.append((danger_button if destructive else primary_button)(save_text, on_click=save))
        dialog.actions = actions
        guard_tree(dialog)
        dialog.open = True
        page.dialog = dialog
        page.update()

    def confirm(title: str, message: str, action: Callable, action_text: str = "Confirm"):
        open_dialog(title, [ft.Text(message, color=C.slate)], lambda e: action(), action_text, destructive=True)

    def error_state(title: str, message: str):
        return ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CLOUD_OFF, size=54, color=C.red),
                    ft.Text(title, size=24, weight=ft.FontWeight.W_800, color=C.ink),
                    ft.Text(message, size=13, color=C.muted, text_align=ft.TextAlign.CENTER),
                    primary_button("Retry", ft.Icons.REFRESH, lambda e: refresh()),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                width=520,
            ),
        )

    def empty_state(title: str, message: str, icon=ft.Icons.INVENTORY_2_OUTLINED):
        return ft.Container(
            padding=32,
            alignment=ft.alignment.center,
            content=ft.Column(
                [ft.Icon(icon, size=44, color=C.muted), ft.Text(title, size=18, weight=ft.FontWeight.W_700, color=C.ink), ft.Text(message, size=12, color=C.muted, text_align=ft.TextAlign.CENTER)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
        )

    def field_error(field: ft.TextField | ft.Dropdown, message: str):
        field.error_text = message
        page.update()

    def require_text(field: ft.TextField, label: str) -> str:
        value = (field.value or "").strip()
        field.error_text = None
        if not value:
            field_error(field, f"{label} is required.")
            raise ValueError(f"{label} is required.")
        return value

    def read_int(field: ft.TextField, label: str, minimum: int | None = None, maximum: int | None = None) -> int:
        field.error_text = None
        try:
            value = int((field.value or "").strip())
        except Exception as ex:
            field_error(field, f"{label} must be a whole number.")
            raise ValueError(f"{label} must be a whole number.") from ex
        if minimum is not None and value < minimum:
            field_error(field, f"{label} must be at least {minimum}.")
            raise ValueError(f"{label} must be at least {minimum}.")
        if maximum is not None and value > maximum:
            field_error(field, f"{label} must be at most {maximum}.")
            raise ValueError(f"{label} must be at most {maximum}.")
        return value

    def read_float(field: ft.TextField, label: str, minimum: float | None = None) -> float:
        field.error_text = None
        try:
            value = float((field.value or "").strip())
        except Exception as ex:
            field_error(field, f"{label} must be numeric.")
            raise ValueError(f"{label} must be numeric.") from ex
        if minimum is not None and value < minimum:
            field_error(field, f"{label} must be at least {minimum}.")
            raise ValueError(f"{label} must be at least {minimum}.")
        return value

    def get_all(resource: str, **params) -> list[dict]:
        return safe_items(state.client.page(resource, limit=200, **params))

    def id_options(rows: list[dict], label_keys: list[str], id_key: str) -> dict[str, str]:
        result = {}
        for row in rows:
            label = " / ".join(str(row.get(key) or "") for key in label_keys if row.get(key) is not None)
            result[label] = row[id_key]
        return result

    def dashboard_card(title: str, value: str, subtitle: str, icon, tone: str = "blue"):
        tones = {
            "blue": (C.blue, C.blue_soft),
            "green": (C.green, C.green_soft),
            "red": (C.red, C.red_soft),
            "amber": (C.amber, C.amber_soft),
            "purple": (C.purple, C.purple_soft),
            "slate": (C.slate, C.slate_soft),
        }
        fg, bg = tones.get(tone, tones["blue"])
        return panel(
            ft.Column(
                [
                    ft.Row([ft.Container(width=38, height=38, alignment=ft.alignment.center, border_radius=12, bgcolor=bg, content=ft.Icon(icon, color=fg, size=20)), ft.Container(expand=True), ft.Text(title, size=12, color=C.muted, weight=ft.FontWeight.W_600)], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(value, size=27, weight=ft.FontWeight.W_800, color=C.ink),
                    ft.Text(subtitle, size=12, color=C.muted),
                ],
                spacing=8,
            ),
            expand=True,
        )

    def slot_tile(slot: dict, size: int = 52):
        status = slot.get("status") or "Unknown"
        fg, bg = STATUS_COLORS.get(status, (C.slate, C.slate_soft))
        border_color = fg if status in ("Occupied", "Reserved", "Maintenance", "Disabled") else "#B7E4C7"
        return ft.Container(
            width=size + 10,
            height=size,
            border_radius=12,
            bgcolor=bg,
            border=ft.border.all(1, border_color),
            alignment=ft.alignment.center,
            tooltip=f"{slot.get('slot_code')} · {status} · {slot.get('slot_type')}",
            on_click=lambda e, row=slot: open_slot_drawer(row.get("slot_id")),
            content=ft.Column(
                [
                    ft.Text(slot.get("slot_code", ""), size=11, weight=ft.FontWeight.W_800, color=fg),
                    ft.Text(str(slot.get("slot_type", ""))[:2].upper(), size=9, color=fg),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

    def legend():
        items = []
        for status in SLOT_STATUSES:
            fg, bg = STATUS_COLORS[status]
            items.append(ft.Row([ft.Container(width=10, height=10, border_radius=99, bgcolor=fg), ft.Text(status, size=11, color=C.muted)], spacing=6, tight=True))
        return ft.Row(items, spacing=14, wrap=True)

    def mini_bars(points: list[dict], value_key: str = "revenue", label_key: str = "day", height: int = 132):
        if not points:
            return empty_state("No chart data yet", "Complete and pay sessions to populate this chart.", ft.Icons.BAR_CHART)
        ordered = list(reversed(points))
        max_value = max(float(row.get(value_key) or 0) for row in ordered) or 1
        bars = []
        for row in ordered:
            raw = float(row.get(value_key) or 0)
            bar_height = max(12, int((raw / max_value) * (height - 34)))
            label = str(row.get(label_key) or "")[-5:]
            bars.append(ft.Column([ft.Container(width=30, height=bar_height, border_radius=8, bgcolor=C.blue), ft.Text(label, size=10, color=C.muted)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.END, spacing=6))
        return ft.Container(height=height, content=ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_AROUND, vertical_alignment=ft.CrossAxisAlignment.END))

    def table(columns: list[str], rows: list[dict], keys: list[str], actions: Callable[[dict], ft.Control] | None = None, empty_title: str = "No records"):
        if not rows:
            return panel(empty_state(empty_title, "The dataset is currently empty or filtered out."), expand=True)
        data_rows = []
        for row in rows:
            cells = []
            for key in keys:
                value = row.get(key, "")
                if "time" in key or key.endswith("_at"):
                    value = compact_time(value)
                if key in ("status", "payment_status", "last_status"):
                    cells.append(ft.DataCell(badge(value)))
                else:
                    cells.append(ft.DataCell(ft.Text(str(value if value is not None else ""), size=12, color=C.ink)))
            if actions:
                cells.append(ft.DataCell(actions(row)))
            data_rows.append(ft.DataRow(cells=cells))
        data_columns = [ft.DataColumn(ft.Text(name, weight=ft.FontWeight.W_700, color=C.slate, size=12)) for name in columns]
        if actions:
            data_columns.append(ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.W_700, color=C.slate, size=12)))
        return panel(
            ft.Row(
                [ft.DataTable(columns=data_columns, rows=data_rows, heading_row_height=42, data_row_min_height=48, column_spacing=22, horizontal_margin=12, divider_thickness=0.5)],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=8,
            expand=True,
        )

    def render_login():
        email = text_input("Email", "admin@smartpark.com", width=370, helper="Demo account is available for the judge.")
        password = text_input("Password", "admin1234", width=370, password=True)
        status = ft.Text("", color=C.red, size=12)
        login_button = primary_button("Sign in", ft.Icons.LOGIN, width=370)

        def set_loading(is_loading: bool):
            login_button.disabled = is_loading
            login_button.text = "Signing in..." if is_loading else "Sign in"
            page.update()

        def do_login(_):
            status.value = ""
            try:
                set_loading(True)
                state.login(state.client.login(require_text(email, "Email"), require_text(password, "Password")))
                refresh()
            except Exception as ex:
                status.value = str(ex)
                set_loading(False)
                page.update()

        login_button.on_click = do_login
        hero = ft.Container(
            expand=True,
            padding=56,
            gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=["#0F3D91", "#2563EB", "#5EA2FF"]),
            content=ft.Column(
                [
                    ft.Container(width=54, height=54, border_radius=16, bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE), alignment=ft.alignment.center, content=ft.Icon(ft.Icons.LOCAL_PARKING, size=30, color=ft.Colors.WHITE)),
                    ft.Text("SmartPark", size=42, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
                    ft.Text("Smart Parking Slot Optimizer", size=18, weight=ft.FontWeight.W_600, color="#DCEBFF"),
                    ft.Text("A complete demo operations console for live occupancy, optimized assignment, sensor supervision, tariffs, payments, and reporting.", size=14, color="#EAF2FF", width=470),
                    ft.Container(height=24),
                    ft.Row([badge("Real-time slots"), badge("Tariff snapshots"), badge("Sensor-aware")], spacing=10),
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )
        form = ft.Container(
            width=520,
            padding=42,
            bgcolor=C.panel,
            content=ft.Column(
                [
                    ft.Text("Admin sign in", size=30, weight=ft.FontWeight.W_900, color=C.ink),
                    ft.Text("Use the seeded demo credentials. Registration is disabled in the operator console.", size=13, color=C.muted),
                    ft.Container(height=8),
                    email,
                    password,
                    login_button,
                    ft.Container(padding=14, border_radius=14, bgcolor=C.blue_soft, content=ft.Text("Demo credentials: admin@smartpark.com / admin1234", size=12, color=C.blue_dark, weight=ft.FontWeight.W_600)),
                    status,
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )
        page.add(ft.Row([hero, form], expand=True))
        page.update()

    def sidebar():
        tiles = []
        for name, icon in nav_items:
            selected = state.view == name
            tiles.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=11),
                    border_radius=12,
                    bgcolor=C.blue_soft if selected else None,
                    on_click=lambda e, n=name: switch_view(n),
                    content=ft.Row([ft.Icon(icon, size=20, color=C.blue if selected else C.slate), ft.Text(name, size=13, weight=ft.FontWeight.W_700 if selected else ft.FontWeight.W_500, color=C.blue if selected else C.slate)], spacing=10),
                )
            )
        user = state.user or {}
        return ft.Container(
            width=250,
            bgcolor=C.panel,
            padding=20,
            border=ft.border.only(right=ft.BorderSide(1, C.line)),
            content=ft.Column(
                [
                    ft.Row([ft.Container(width=38, height=38, border_radius=12, bgcolor=C.blue, alignment=ft.alignment.center, content=ft.Icon(ft.Icons.LOCAL_PARKING, color=ft.Colors.WHITE)), ft.Column([ft.Text("SmartPark", size=19, weight=ft.FontWeight.W_900, color=C.ink), ft.Text("Operations Console", size=11, color=C.muted)], spacing=0)], spacing=10),
                    ft.Container(height=12),
                    *tiles,
                    ft.Container(expand=True),
                    ft.Container(padding=14, border_radius=16, bgcolor=C.soft, content=ft.Column([ft.Text(user.get("full_name", "Admin"), weight=ft.FontWeight.W_700, color=C.ink), ft.Text(user.get("email", ""), size=11, color=C.muted), secondary_button("Logout", ft.Icons.LOGOUT, lambda e: logout(), width=190)], spacing=8)),
                ],
                spacing=8,
            ),
        )

    def topbar():
        search = text_input("Search slots, vehicles, sessions", state.global_search_query, width=360)

        def submit(_):
            state.global_search_query = search.value or ""
            global_search_modal(state.global_search_query)

        search.on_submit = submit
        return ft.Container(
            height=78,
            padding=ft.padding.symmetric(horizontal=28, vertical=16),
            bgcolor=C.soft,
            content=ft.Row(
                [
                    ft.Column([ft.Text(state.view, size=24, weight=ft.FontWeight.W_900, color=C.ink), ft.Text("Local demo environment · FastAPI + SQLite + Flet", size=12, color=C.muted)], spacing=1),
                    ft.Container(expand=True),
                    search,
                    secondary_button("Search", ft.Icons.SEARCH, submit),
                    secondary_button("Refresh", ft.Icons.REFRESH, lambda e: refresh()),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
            ),
        )

    def global_search_modal(query: str):
        term = (query or "").strip()
        if not term:
            notify("Enter a slot, plate, sensor, or session search term.", True)
            return
        slots = get_all("slots", search=term)
        sessions = get_all("sessions", search=term)
        vehicles = get_all("vehicles", search=term)
        sensors = get_all("sensors", search=term)
        def slot_rows():
            if not slots:
                return empty_state("No slot matches", "Try another slot code, zone, or lot name.", ft.Icons.LOCAL_PARKING)
            return ft.Column([ft.Container(padding=10, border_radius=12, bgcolor=C.soft, on_click=lambda e, row=row: open_slot_drawer(row["slot_id"]), content=ft.Row([ft.Text(row["slot_code"], width=80, weight=ft.FontWeight.W_800, color=C.ink), badge(row["status"]), ft.Text(f"{row.get('lot_name')} / {row.get('zone_name')}", size=12, color=C.muted, expand=True)])) for row in slots[:8]], spacing=8)
        body = ft.Column([
            section_title("Global search", f"Results for {term}"),
            ft.Text("Slots", weight=ft.FontWeight.W_800, color=C.ink),
            slot_rows(),
            ft.Text("Sessions", weight=ft.FontWeight.W_800, color=C.ink),
            table(["Plate", "Slot", "Status", "Payment"], sessions[:6], ["plate_number", "slot_code", "status", "payment_status"], None, "No session matches"),
            ft.Text("Vehicles and sensors", weight=ft.FontWeight.W_800, color=C.ink),
            ft.Row([table(["Plate", "Type", "Owner"], vehicles[:5], ["plate_number", "vehicle_type", "owner_name"], None, "No vehicle matches"), table(["Sensor", "Slot", "Status"], sensors[:5], ["sensor_code", "slot_code", "last_status"], None, "No sensor matches")], spacing=12),
        ], spacing=12)
        open_dialog("Search results", [body], None, width=860)

    def shell():
        drawer = slot_detail_panel() if state.selected_slot_id else None
        main_content = ft.Container(expand=True, padding=ft.padding.only(left=28, right=28, bottom=28), content=current_view())
        body_controls = [main_content]
        if drawer:
            body_controls.append(drawer)
        return ft.Row([sidebar(), ft.Column([topbar(), ft.Row(body_controls, expand=True, spacing=0)], expand=True)], expand=True)

    def current_view():
        try:
            if state.view == "Dashboard":
                return dashboard_view()
            if state.view == "Zone Management":
                return zone_management_view()
            if state.view == "Sessions & Payments":
                return sessions_payments_view()
            if state.view == "Forms Library":
                return forms_library_view()
            if state.view == "System Configuration":
                return system_configuration_view()
            return reports_view()
        except ApiError as ex:
            return error_state("Backend request failed", str(ex))
        except Exception as ex:
            return error_state("Screen could not render", str(ex))

    def dashboard_view():
        data = state.client.dashboard()
        stats = data.get("slot_stats", {})
        active = safe_items(state.client.page("sessions", status_filter="Active", limit=8))
        cards = ft.Row(
            [
                dashboard_card("Total revenue", money(data.get("total_revenue")), "Paid sessions collected", ft.Icons.PAYMENTS, "green"),
                dashboard_card("Occupancy rate", percent(data.get("occupancy_rate")), "Occupied over total slots", ft.Icons.LOCAL_PARKING, "blue"),
                dashboard_card("Active sessions", str(data.get("active_sessions", 0)), "Vehicles currently parked", ft.Icons.TIMER_OUTLINED, "purple"),
                dashboard_card("Available slots", str(stats.get("available_slots") or 0), "Ready for assignment", ft.Icons.EVENT_AVAILABLE, "green"),
                dashboard_card("Sensors online", f"{data.get('sensors_online', 0)}/{data.get('sensors_total', 0)}", "Fault and battery aware", ft.Icons.SENSORS, "amber" if data.get("sensors_online", 0) < data.get("sensors_total", 0) else "blue"),
                dashboard_card("Payment due", money(data.get("payment_due")), "Completed sessions awaiting settlement", ft.Icons.RECEIPT_LONG, "red" if data.get("payment_due") else "slate"),
            ],
            spacing=14,
        )
        quick_actions = ft.Row(
            [
                primary_button("New session", ft.Icons.ADD, lambda e: session_form()),
                secondary_button("Emergency exit", ft.Icons.EMERGENCY, lambda e: emergency_exit_form()),
                secondary_button("Bulk create slots", ft.Icons.TABLE_ROWS, lambda e: bulk_slots_form()),
                secondary_button("Export report", ft.Icons.FILE_DOWNLOAD, lambda e: export_report_modal()),
                secondary_button("Add slot", ft.Icons.LOCAL_PARKING, lambda e: slot_form()),
            ],
            spacing=10,
        )
        slot_map = data.get("slot_map", [])
        map_panel = panel(
            ft.Column(
                [section_title("Real-time occupancy map", "Click any slot for the operational drawer."), legend(), ft.Row([slot_tile(slot) for slot in slot_map[:120]], wrap=True, spacing=8, run_spacing=8)],
                spacing=14,
            ),
            expand=2,
        )
        revenue_panel = panel(ft.Column([section_title("Revenue visibility", "Paid revenue by recent day."), mini_bars(data.get("revenue_series", [])), ft.Text(f"Unpaid exposure: {money(data.get('payment_due'))}", size=12, color=C.muted)], spacing=12), expand=1)
        sessions_panel = panel(
            ft.Column(
                [
                    section_title("Active sessions", "Current vehicles inside the facility."),
                    *(active_session_line(row) for row in active),
                    secondary_button("View all sessions", ft.Icons.OPEN_IN_FULL, lambda e: switch_view("Sessions & Payments"), width=190),
                ] if active else [section_title("Active sessions", "Current vehicles inside the facility."), empty_state("No active sessions", "Start an optimized session to populate this panel.", ft.Icons.TIMER_OUTLINED)],
                spacing=12,
            ),
            expand=1,
        )
        alerts_panel = panel(ft.Column([section_title("Operational alerts", "Issues that need operator attention."), *[alert_line(item) for item in data.get("alerts", [])], ft.Divider(height=10, color=C.line), section_title("Recommended assignments", "Best available slots by priority and distance."), *[suggestion_line(item) for item in data.get("optimizer_suggestions", [])]], spacing=12), expand=1)
        return ft.Column([quick_actions, cards, ft.Row([map_panel, revenue_panel], spacing=14), ft.Row([sessions_panel, alerts_panel], spacing=14)], spacing=16, scroll=ft.ScrollMode.AUTO)

    def active_session_line(row: dict):
        return ft.Container(
            padding=12,
            border_radius=14,
            bgcolor=C.soft,
            content=ft.Row([ft.Icon(ft.Icons.DIRECTIONS_CAR, color=C.blue), ft.Column([ft.Text(row.get("plate_number", ""), weight=ft.FontWeight.W_800, color=C.ink), ft.Text(f"{row.get('slot_code')} · entered {compact_time(row.get('entry_time'))}", size=11, color=C.muted)], spacing=1), ft.Container(expand=True), badge(row.get("status", "Active"))], spacing=10),
        )

    def alert_line(message: str):
        critical = "fault" in message.lower() or "payment" in message.lower() or "above" in message.lower()
        return ft.Container(padding=12, border_radius=14, bgcolor=C.amber_soft if critical else C.green_soft, content=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER if critical else ft.Icons.CHECK_CIRCLE, color=C.amber if critical else C.green, size=18), ft.Text(message, size=12, color=C.ink, expand=True)], spacing=8))

    def suggestion_line(row: dict):
        return ft.Container(padding=10, border_radius=12, border=ft.border.all(1, C.line), content=ft.Row([ft.Icon(ft.Icons.LOCAL_PARKING, size=18, color=C.blue), ft.Column([ft.Text(row.get("slot_code", ""), weight=ft.FontWeight.W_800, color=C.ink), ft.Text(f"{row.get('lot_name')} / {row.get('zone_name')} · {row.get('slot_type')}", size=11, color=C.muted)], spacing=1), ft.Container(expand=True), ft.Text(f"P{row.get('priority_score')}", size=11, color=C.muted)], spacing=8))

    def zone_management_view():
        lots = get_all("lots")
        zones = get_all("zones")
        slots = get_all("slots", search=state.search_query)
        if lots and (not state.selected_lot_id or state.selected_lot_id not in [lot["lot_id"] for lot in lots]):
            state.selected_lot_id = lots[0]["lot_id"]
        visible_zones = [zone for zone in zones if not state.selected_lot_id or zone.get("lot_id") == state.selected_lot_id]
        if visible_zones and (not state.selected_zone_id or state.selected_zone_id not in [zone["zone_id"] for zone in visible_zones]):
            state.selected_zone_id = visible_zones[0]["zone_id"]
        lot_labels = {lot["name"]: lot["lot_id"] for lot in lots}
        zone_labels = {f"{zone['lot_name']} / {zone['name']}": zone["zone_id"] for zone in visible_zones}
        selected_lot_name = next((name for name, lid in lot_labels.items() if lid == state.selected_lot_id), next(iter(lot_labels), ""))
        selected_zone_label = next((label for label, zid in zone_labels.items() if zid == state.selected_zone_id), next(iter(zone_labels), ""))
        lot_select = select_input("Parking lot", list(lot_labels.keys()), selected_lot_name, width=250)
        zone_select = select_input("Zone", list(zone_labels.keys()), selected_zone_label, width=290)
        slot_search = text_input("Search slots", state.slot_search_query, width=220)
        status_filter = select_input("Status", ["All"] + SLOT_STATUSES, "All", width=180)
        grid_holder = ft.Column(spacing=12, expand=True)
        cards_holder = ft.Row(wrap=True, spacing=12, run_spacing=12)

        def current_zone():
            return next((zone for zone in zones if zone.get("zone_id") == state.selected_zone_id), None)

        def load_zone_body(update: bool = True):
            state.slot_search_query = slot_search.value or ""
            state.selected_lot_id = lot_labels.get(lot_select.value or "")
            visible = [zone for zone in zones if not state.selected_lot_id or zone.get("lot_id") == state.selected_lot_id]
            zone_options = {f"{zone['lot_name']} / {zone['name']}": zone["zone_id"] for zone in visible}
            zone_select.options = [ft.dropdown.Option(label) for label in zone_options]
            if zone_select.value not in zone_options and zone_options:
                zone_select.value = next(iter(zone_options))
            state.selected_zone_id = zone_options.get(zone_select.value or "")
            cards_holder.controls = [zone_card(zone) for zone in visible]
            zone_slots = [slot for slot in get_all("slots", search=state.slot_search_query, zone_id=state.selected_zone_id) if status_filter.value == "All" or slot.get("status") == status_filter.value]
            summary = status_summary(zone_slots)
            grid_holder.controls = [ft.Row(summary, spacing=10, wrap=True), ft.Row([slot_tile(slot, 56) for slot in zone_slots], wrap=True, spacing=9, run_spacing=9)] if zone_slots else [empty_state("No slots match this view", "Adjust the lot, zone, status, or search filter, then try again.", ft.Icons.LOCAL_PARKING)]
            if update:
                page.update()

        def select_zone(zone_id: str):
            state.selected_zone_id = zone_id
            for label, zid in zone_labels.items():
                if zid == zone_id:
                    zone_select.value = label
            load_zone_body()

        def zone_card(zone: dict):
            zone_slots = [slot for slot in slots if slot.get("zone_id") == zone.get("zone_id")]
            total = len(zone_slots)
            occupied = sum(1 for slot in zone_slots if slot.get("status") == "Occupied")
            available = sum(1 for slot in zone_slots if slot.get("status") == "Available")
            rate = round(occupied / total * 100, 1) if total else 0
            selected = zone.get("zone_id") == state.selected_zone_id
            return ft.Container(
                width=270,
                padding=16,
                border_radius=18,
                bgcolor=C.blue_soft if selected else C.panel,
                border=ft.border.all(1.5 if selected else 1, C.blue if selected else C.line),
                on_click=lambda e, zid=zone["zone_id"]: select_zone(zid),
                content=ft.Column([
                    ft.Row([ft.Text(zone.get("name", ""), size=16, weight=ft.FontWeight.W_800, color=C.ink), ft.Container(expand=True), badge(zone.get("zone_type", "Standard"))]),
                    ft.Text(f"{zone.get('lot_name')} · Floor {zone.get('floor_level')}", size=11, color=C.muted),
                    ft.Row([metric_pill("Total", total), metric_pill("Open", available), metric_pill("Used", f"{rate}%")], spacing=8),
                    ft.ProgressBar(value=rate / 100 if total else 0, color=C.blue, bgcolor=C.slate_soft),
                    ft.Row([ft.TextButton("Edit", icon=ft.Icons.EDIT, on_click=lambda e, z=zone: zone_form(z)), ft.TextButton("Delete", icon=ft.Icons.DELETE_OUTLINE, style=ft.ButtonStyle(color=C.red), on_click=lambda e, z=zone: confirm("Delete zone", f"Delete zone {z.get('name')}? Existing slots will block this safely.", lambda: delete_resource("zones", z["zone_id"])))], alignment=ft.MainAxisAlignment.END),
                ], spacing=10),
            )

        def add_slot_selected(_):
            zone = current_zone()
            slot_form({"zone_id": state.selected_zone_id} if zone else None)

        def on_lot_change(_):
            state.selected_lot_id = lot_labels.get(lot_select.value or "")
            state.selected_zone_id = None
            load_zone_body()

        def on_zone_change(_):
            state.selected_zone_id = zone_labels.get(zone_select.value or "")
            load_zone_body()

        lot_select.on_change = on_lot_change
        zone_select.on_change = on_zone_change
        slot_search.on_submit = lambda e: load_zone_body()
        slot_search.on_change = lambda e: load_zone_body()
        status_filter.on_change = lambda e: load_zone_body()
        header = ft.Row([section_title("Zone management", "Select a lot, inspect utilization, and operate slots from a live grid."), ft.Container(expand=True), primary_button("Add zone", ft.Icons.ADD, lambda e: zone_form()), secondary_button("Add slot", ft.Icons.LOCAL_PARKING, add_slot_selected), secondary_button("Bulk create", ft.Icons.TABLE_ROWS, lambda e: bulk_slots_form())], vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True)
        load_zone_body(False)
        return ft.Column([header, panel(ft.Row([lot_select, zone_select, slot_search, status_filter, secondary_button("Apply", ft.Icons.SEARCH, lambda e: load_zone_body())], spacing=12, wrap=True), padding=14), cards_holder, panel(ft.Column([ft.Row([section_title("Selected zone slot grid", "Click a bay to open the operational side panel."), ft.Container(expand=True), legend()]), grid_holder], spacing=14), expand=True)], spacing=16, scroll=ft.ScrollMode.AUTO)

    def metric_pill(label: str, value: Any):
        return ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=8), border_radius=12, bgcolor=C.soft, content=ft.Column([ft.Text(str(value), weight=ft.FontWeight.W_800, color=C.ink), ft.Text(label, size=10, color=C.muted)], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

    def status_summary(slots: list[dict]) -> list[ft.Control]:
        return [dashboard_card(status, str(sum(1 for slot in slots if slot.get("status") == status)), "Current zone", ft.Icons.LOCAL_PARKING, "green" if status == "Available" else "red" if status == "Occupied" else "amber" if status == "Reserved" else "slate") for status in SLOT_STATUSES]

    def open_slot_drawer(slot_id: str | None):
        if not slot_id:
            return
        state.selected_slot_id = slot_id
        refresh()

    def close_slot_drawer(_=None):
        state.selected_slot_id = None
        refresh()

    def slot_detail_panel():
        if not state.selected_slot_id:
            return None
        try:
            detail = state.client.slot_detail(state.selected_slot_id)
        except Exception as ex:
            return ft.Container(
                width=430,
                padding=18,
                bgcolor=C.panel,
                border=ft.border.only(left=ft.BorderSide(1, C.line)),
                content=ft.Column([
                    ft.Row([ft.Text("Slot detail", size=20, weight=ft.FontWeight.W_900, color=C.ink), ft.Container(expand=True), ft.IconButton(ft.Icons.CLOSE, on_click=close_slot_drawer)]),
                    error_state("Slot detail unavailable", str(ex)),
                ], spacing=12),
            )
        slot = detail["slot"]
        sensor = detail.get("sensor")
        active = detail.get("active_session")
        slot_type = select_input("Slot type", SLOT_TYPES, slot.get("slot_type"), width=180)
        status_field = select_input("Status", SLOT_STATUSES, slot.get("status"), width=180)
        reason = text_input("Override reason", slot.get("override_reason") or "Operator panel update", width=380)
        priority = text_input("Priority score", str(slot.get("priority_score", 50)), width=180)
        distance = text_input("Distance score", str(slot.get("distance_score", 50)), width=180)
        has_active = active is not None

        def drawer_action_status(new_status: str):
            try:
                state.client.post(f"/slots/{state.selected_slot_id}/status", {"status": new_status, "reason": f"Slot detail action: {new_status}"})
                notify(f"Slot marked {new_status}.")
                refresh()
            except Exception as ex:
                notify(str(ex), True)

        def save(_):
            try:
                state.client.update("slots", state.selected_slot_id, {"slot_type": slot_type.value, "distance_score": read_int(distance, "Distance score", 0, 100), "priority_score": read_int(priority, "Priority score", 0, 100)})
                if status_field.value != slot.get("status"):
                    state.client.post(f"/slots/{state.selected_slot_id}/status", {"status": status_field.value, "reason": require_text(reason, "Override reason")})
                notify("Slot detail saved.")
                refresh()
            except Exception as ex:
                notify(str(ex), True)

        def controlled_button(label: str, icon, status: str, destructive: bool = False):
            button = (danger_button if destructive else secondary_button)(label, icon, lambda e, st=status: drawer_action_status(st), width=185)
            if has_active and status != "Occupied":
                button.disabled = True
                button.tooltip = "End or cancel the active session before this action."
            return button

        conflict = None
        if sensor and sensor.get("last_status") == "Occupied" and not active:
            conflict = ft.Container(padding=12, border_radius=14, bgcolor=C.amber_soft, content=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=C.amber), ft.Text("Sensor reports occupied but no active session is attached. Verify the bay physically before assignment.", size=12, color=C.ink, expand=True)], spacing=8))
        if sensor and sensor.get("last_status") == "Clear" and active:
            conflict = ft.Container(padding=12, border_radius=14, bgcolor=C.amber_soft, content=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=C.amber), ft.Text("Active session exists while sensor reports clear. Check sensor alignment or vehicle position.", size=12, color=C.ink, expand=True)], spacing=8))

        score_card = ft.Container(
            padding=14,
            border_radius=16,
            bgcolor=C.soft,
            content=ft.Row([
                metric_pill("Priority", slot.get("priority_score")),
                metric_pill("Distance", slot.get("distance_score")),
                metric_pill("Sensor", sensor.get("last_status") if sensor else "None"),
            ], spacing=8),
        )
        controls = [
            ft.Row([ft.Column([ft.Text(slot.get("slot_code", ""), size=28, weight=ft.FontWeight.W_900, color=C.ink), ft.Text(f"{slot.get('lot_name')} / {slot.get('zone_name')}", color=C.muted)], spacing=1), ft.Container(expand=True), badge(slot.get("status")), ft.IconButton(ft.Icons.CLOSE, on_click=close_slot_drawer)]),
            score_card,
        ]
        if conflict:
            controls.append(conflict)
        controls.extend([
            section_title("Configuration", "Operational fields and assignment scoring."),
            ft.Row([slot_type, status_field], spacing=12),
            ft.Row([priority, distance], spacing=12),
            reason,
            primary_button("Save changes", ft.Icons.SAVE, save, width=185),
            ft.Divider(color=C.line),
            section_title("Current vehicle/session", "Live occupancy context for this slot."),
            session_summary(active),
            section_title("Sensor assignment", "Hardware link and latest health signal."),
            sensor_summary(sensor, state.selected_slot_id),
            ft.Row([secondary_button("Assign sensor", ft.Icons.SENSORS, lambda e: assign_sensor_form(state.selected_slot_id), width=185), controlled_button("Reserve", ft.Icons.LOCK, "Reserved")], wrap=True, spacing=8),
            ft.Row([controlled_button("Release", ft.Icons.CHECK_CIRCLE, "Available"), controlled_button("Maintenance", ft.Icons.BUILD_OUTLINED, "Maintenance", True)], wrap=True, spacing=8),
            ft.Divider(color=C.line),
            section_title("Recent activity", "Slot, sensor, session, and payment events."),
            activity_list(detail.get("activity", []), detail.get("recent_sessions", []), detail.get("sensor_events", [])),
        ])
        return ft.Container(
            width=460,
            bgcolor=C.panel,
            padding=18,
            border=ft.border.only(left=ft.BorderSide(1, C.line)),
            content=ft.Column(controls, spacing=13, scroll=ft.ScrollMode.AUTO),
        )

    def session_summary(active: dict | None):
        if not active:
            return ft.Container(padding=14, border_radius=14, bgcolor=C.green_soft, content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color=C.green), ft.Text("No active session is attached to this slot.", color=C.ink)], spacing=8))
        return ft.Container(padding=14, border_radius=14, bgcolor=C.red_soft, content=ft.Column([ft.Row([ft.Icon(ft.Icons.DIRECTIONS_CAR, color=C.red), ft.Text(active.get("plate_number", ""), weight=ft.FontWeight.W_800, color=C.ink), badge(active.get("status", "Active"))]), ft.Text(f"Type: {active.get('vehicle_type')} · Entry: {compact_time(active.get('entry_time'))}", size=12, color=C.muted), ft.Row([secondary_button("Exit session", ft.Icons.OUTPUT, lambda e, row=active: exit_session_form(row)), secondary_button("Open payment flow", ft.Icons.PAYMENTS, lambda e: switch_view("Sessions & Payments"))], spacing=8)], spacing=8))

    def sensor_summary(sensor: dict | None, slot_id: str):
        if not sensor:
            return ft.Container(padding=14, border_radius=14, bgcolor=C.slate_soft, content=ft.Row([ft.Icon(ft.Icons.SENSORS_OFF, color=C.slate), ft.Text("No sensor assigned. Use Assign sensor to link an existing node.", color=C.ink, expand=True)], spacing=8))
        active_text = "Online" if sensor.get("is_active") else "Inactive"
        def unassign(_):
            try:
                state.client.update("sensors", sensor["sensor_id"], {"slot_id": None, "sensor_code": sensor["sensor_code"], "sensor_type": sensor["sensor_type"], "is_active": bool(sensor["is_active"]), "battery_level": sensor["battery_level"]})
                notify("Sensor unassigned from slot.")
                refresh()
            except Exception as ex:
                notify(str(ex), True)
        return ft.Container(padding=14, border_radius=14, bgcolor=C.soft, content=ft.Column([ft.Row([ft.Icon(ft.Icons.SENSORS, color=C.blue), ft.Text(sensor.get("sensor_code", ""), weight=ft.FontWeight.W_800, color=C.ink), badge(sensor.get("last_status", "Unknown"))]), ft.Text(f"{active_text} · Battery {sensor.get('battery_level')}% · Last seen {compact_time(sensor.get('last_seen_at'))}", size=12, color=C.muted), ft.Row([secondary_button("Simulate clear", ft.Icons.CHECK_CIRCLE, lambda e, s=sensor: simulate_sensor_action(s, "Clear")), secondary_button("Simulate occupied", ft.Icons.LOCAL_PARKING, lambda e, s=sensor: simulate_sensor_action(s, "Occupied")), danger_button("Fault", ft.Icons.WARNING_AMBER, lambda e, s=sensor: simulate_sensor_action(s, "Fault")), secondary_button("Unassign", ft.Icons.LINK_OFF, unassign)], spacing=8, wrap=True)], spacing=8))

    def activity_list(activity: list[dict], sessions: list[dict], events: list[dict]):
        controls = []
        for item in activity[:8]:
            controls.append(ft.Container(padding=10, border_radius=12, border=ft.border.all(1, C.line), content=ft.Column([ft.Row([badge(item.get("severity", "Info")), ft.Text(compact_time(item.get("created_at")), size=10, color=C.muted)]), ft.Text(item.get("title", ""), weight=ft.FontWeight.W_700, color=C.ink), ft.Text(item.get("message", ""), size=11, color=C.muted)], spacing=3)))
        if not controls:
            for item in sessions[:4]:
                controls.append(ft.Text(f"{item.get('plate_number')} · {item.get('status')} · {compact_time(item.get('entry_time'))}", size=12, color=C.muted))
            for item in events[:4]:
                controls.append(ft.Text(f"Sensor {item.get('reported_status')} · {compact_time(item.get('created_at'))}", size=12, color=C.muted))
        return ft.Column(controls if controls else [ft.Text("No activity has been recorded for this slot yet.", size=12, color=C.muted)], spacing=8)

    def sessions_payments_view():
        reports = state.client.report_summary()
        search = text_input("Search plate, slot, session", state.session_search_query, width=260)
        status_filter = select_input("Session status", SESSION_STATUSES, "All", width=190)
        payment_filter = select_input("Payment status", PAYMENT_STATUSES, "All", width=190)
        results_holder = ft.Column(expand=True)

        def load(update: bool = True):
            state.session_search_query = search.value or ""
            params = {"search": state.session_search_query}
            if status_filter.value != "All":
                params["status_filter"] = status_filter.value
            rows = get_all("sessions", **params)
            if payment_filter.value != "All":
                rows = [row for row in rows if row.get("payment_status") == payment_filter.value]
            results_holder.controls = [table(["Plate", "Type", "Slot", "Entry", "Exit", "Status", "Fee", "Payment"], rows, ["plate_number", "vehicle_type", "slot_code", "entry_time", "exit_time", "status", "fee_amount", "payment_status"], session_actions, "No sessions match these filters")]
            if update:
                page.update()

        for control in (search, status_filter, payment_filter):
            control.on_change = lambda e: load()
            if hasattr(control, "on_submit"):
                control.on_submit = lambda e: load()

        load(False)
        summaries = ft.Row([dashboard_card("Collected", money(reports.get("total_revenue")), "Paid payment records", ft.Icons.PAYMENTS, "green"), dashboard_card("Average session", f"{reports.get('average_completed_duration_minutes', 0)} min", "Completed sessions", ft.Icons.TIMER_OUTLINED, "blue"), dashboard_card("Session count", str(reports.get("session_count", 0)), "All historical records", ft.Icons.FACT_CHECK, "purple"), dashboard_card("Peak posture", "Ready", "Filters and payment flow online", ft.Icons.ONLINE_PREDICTION, "green")], spacing=14)
        header = ft.Row([section_title("Sessions & payments", "Search, exit vehicles, calculate fees, process payments, and view receipts."), ft.Container(expand=True), primary_button("New session", ft.Icons.ADD, lambda e: session_form())])
        filters = panel(ft.Row([search, status_filter, payment_filter, secondary_button("Apply", ft.Icons.SEARCH, lambda e: load())], spacing=12, wrap=True), padding=14)
        return ft.Column([header, summaries, filters, results_holder], spacing=16, scroll=ft.ScrollMode.AUTO)

    def session_actions(row: dict):
        controls = []
        if row.get("status") == "Active":
            controls.append(ft.IconButton(ft.Icons.OUTPUT, tooltip="Exit session", icon_color=C.blue, on_click=lambda e, r=row: exit_session_form(r)))
            controls.append(ft.IconButton(ft.Icons.CANCEL_OUTLINED, tooltip="Cancel", icon_color=C.red, on_click=lambda e, r=row: confirm("Cancel session", f"Cancel active session for {r.get('plate_number')} in {r.get('slot_code')}?", lambda: cancel_session(r))))
        if row.get("status") == "Completed" and row.get("payment_status") != "Paid":
            controls.append(ft.IconButton(ft.Icons.PAYMENTS, tooltip="Process payment", icon_color=C.green, on_click=lambda e, r=row: payment_form(r)))
        if row.get("status") == "Completed":
            controls.append(ft.IconButton(ft.Icons.RECEIPT_LONG, tooltip="Receipt", icon_color=C.slate, on_click=lambda e, r=row: receipt_modal(r.get("session_id"))))
        return ft.Row(controls, tight=True)

    def forms_library_view():
        cards = [
            form_card("Add Parking Lot", "Create a real facility with address and operator-facing description.", ft.Icons.GARAGE_OUTLINED, lambda e: lot_form()),
            form_card("Add Parking Zone", "Attach a zone to a lot and define floor/type/optimizer priority.", ft.Icons.MAP_OUTLINED, lambda e: zone_form()),
            form_card("Add Parking Slot", "Create a slot with type, status, distance, and priority scoring.", ft.Icons.LOCAL_PARKING, lambda e: slot_form()),
            form_card("Register Hardware Sensor", "Create or assign an ultrasonic sensor node to a bay.", ft.Icons.SENSORS, lambda e: sensor_form()),
            form_card("Create Tariff Plan", "Define rate, grace period, daily max, vehicle and zone applicability.", ft.Icons.PRICE_CHANGE_OUTLINED, lambda e: tariff_form()),
            form_card("Manual Session Entry", "Register a vehicle and start a session with optimized assignment.", ft.Icons.INPUT, lambda e: session_form()),
        ]
        return ft.Column([ft.Row([section_title("Management forms library", "Polished validated forms for demo workflows and judge review."), ft.Container(expand=True), secondary_button("Bulk slot creation", ft.Icons.TABLE_ROWS, lambda e: bulk_slots_form())]), ft.Row(cards, wrap=True, spacing=16, run_spacing=16)], spacing=18, scroll=ft.ScrollMode.AUTO)

    def form_card(title: str, description: str, icon, action):
        return panel(ft.Column([ft.Container(width=44, height=44, border_radius=14, bgcolor=C.blue_soft, alignment=ft.alignment.center, content=ft.Icon(icon, color=C.blue)), ft.Text(title, size=18, weight=ft.FontWeight.W_800, color=C.ink), ft.Text(description, size=12, color=C.muted, height=1.35), ft.Container(expand=True), primary_button("Open form", ft.Icons.OPEN_IN_FULL, action, width=180)], spacing=12), width=330, height=250)

    def system_configuration_view():
        dashboard = state.client.dashboard()
        sensors = get_all("sensors")
        tariffs = get_all("tariffs")
        sensor_table = table(["Code", "Type", "Slot", "Active", "Status", "Battery"], sensors, ["sensor_code", "sensor_type", "slot_code", "is_active", "last_status", "battery_level"], sensor_actions, "No sensors registered")
        tariff_table = table(["Name", "Hourly", "Grace", "Daily Max", "Vehicle", "Zone", "Active"], tariffs, ["name", "hourly_rate", "grace_minutes", "daily_max", "vehicle_type", "zone_name", "is_active"], tariff_actions, "No tariff plans")
        health = ft.Row([dashboard_card("API health", "Online", "FastAPI reachable", ft.Icons.HEALTH_AND_SAFETY, "green"), dashboard_card("Sensors", f"{dashboard.get('sensors_online', 0)}/{dashboard.get('sensors_total', 0)}", "Online ratio", ft.Icons.SENSORS, "blue"), dashboard_card("Slot supply", str(dashboard.get("slot_stats", {}).get("total_slots") or 0), "Physical bays", ft.Icons.LOCAL_PARKING, "purple"), dashboard_card("Payment exposure", money(dashboard.get("payment_due")), "Unsettled completed sessions", ft.Icons.WARNING_AMBER, "amber")], spacing=14)
        settings = panel(ft.Column([section_title("Operations toolkit", "Every control here writes through the API and refreshes the live view."), ft.Container(padding=12, border_radius=14, bgcolor=C.blue_soft, content=ft.Text("Sensor simulation, tariff edits, and bulk slot creation are persisted in SQLite and reflected across Dashboard, Zone Management, and Reports.", size=12, color=C.blue_dark)), ft.Row([primary_button("Bulk create slots", ft.Icons.TABLE_ROWS, lambda e: bulk_slots_form()), secondary_button("Register sensor", ft.Icons.SENSORS, lambda e: sensor_form()), secondary_button("Create tariff", ft.Icons.PRICE_CHANGE_OUTLINED, lambda e: tariff_form())], spacing=10, wrap=True)], spacing=12), expand=True)
        return ft.Column([ft.Row([section_title("System configuration", "Sensor network, tariff plans, health, and demo-safe operations."), ft.Container(expand=True), secondary_button("Refresh", ft.Icons.REFRESH, lambda e: refresh())]), health, settings, ft.Row([ft.Column([section_title("Sensor network", "Simulate status, detect battery issues, edit assignments."), sensor_table], expand=True, spacing=10), ft.Column([section_title("Tariff plans", "Snapshot-backed fee rules used by sessions."), tariff_table], expand=True, spacing=10)], spacing=16)], spacing=16, scroll=ft.ScrollMode.AUTO)

    def sensor_actions(row: dict):
        return ft.Row([ft.IconButton(ft.Icons.SENSORS, tooltip="Simulate", icon_color=C.blue, on_click=lambda e, r=row: simulate_sensor_form(r)), ft.IconButton(ft.Icons.MODE_EDIT_OUTLINE, tooltip="Edit", icon_color=C.slate, on_click=lambda e, r=row: sensor_form(r)), ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Delete", icon_color=C.red, on_click=lambda e, r=row: confirm("Delete sensor", f"Delete sensor {r.get('sensor_code')}? This is blocked if constraints reject it.", lambda: delete_resource("sensors", r["sensor_id"])))], tight=True)

    def tariff_actions(row: dict):
        return ft.Row([ft.IconButton(ft.Icons.MODE_EDIT_OUTLINE, tooltip="Edit", icon_color=C.slate, on_click=lambda e, r=row: tariff_form(r)), ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Delete", icon_color=C.red, on_click=lambda e, r=row: confirm("Delete tariff", f"Delete tariff {r.get('name')}? Historical sessions may block this.", lambda: delete_resource("tariffs", r["tariff_id"])))], tight=True)

    def reports_view():
        report = state.client.report_summary()
        zones = report.get("zone_utilization", [])
        payments = report.get("payments", [])
        max_sessions = max([row.get("session_count") or 0 for row in zones] + [1])
        zone_bars = []
        for row in zones:
            width = max(20, int(((row.get("session_count") or 0) / max_sessions) * 260))
            zone_bars.append(ft.Container(padding=10, border_radius=12, bgcolor=C.soft, content=ft.Row([ft.Text(row.get("zone_name", ""), width=130, color=C.ink, weight=ft.FontWeight.W_700), ft.Container(width=width, height=12, border_radius=8, bgcolor=C.blue), ft.Text(f"{row.get('current_utilization') or 0}%", size=11, color=C.muted)], spacing=8)))
        cards = ft.Row([dashboard_card("Revenue summary", money(report.get("total_revenue")), "Paid payments", ft.Icons.PAYMENTS, "green"), dashboard_card("Occupancy summary", "Live", "See zone utilization", ft.Icons.LOCAL_PARKING, "blue"), dashboard_card("Session count", str(report.get("session_count", 0)), "All sessions", ft.Icons.FACT_CHECK, "purple"), dashboard_card("Average duration", f"{report.get('average_completed_duration_minutes', 0)} min", "Completed sessions", ft.Icons.TIMER_OUTLINED, "amber")], spacing=14)
        return ft.Column([ft.Row([section_title("Reports", "Export-ready revenue, occupancy, zone utilization, and payment history."), ft.Container(expand=True), secondary_button("Export report", ft.Icons.FILE_DOWNLOAD, lambda e: export_report_modal())]), cards, ft.Row([panel(ft.Column([section_title("Zone utilization", "Relative session volume and live utilization."), *zone_bars], spacing=10), expand=1), panel(ft.Column([section_title("Payment history", "Latest settled and attempted payments."), table(["Reference", "Plate", "Method", "Status", "Amount", "Paid at"], payments, ["reference_number", "plate_number", "method", "status", "paid_amount", "paid_at"], None, "No payments yet")], spacing=10), expand=2)], spacing=16)], spacing=16, scroll=ft.ScrollMode.AUTO)

    def lot_form(row: dict | None = None):
        row = row or {}
        is_edit = bool(row.get("lot_id"))
        name = text_input("Lot name", row.get("name", "Harbor Demo Garage"), width=460, helper="Must be unique.")
        address = text_input("Address", row.get("address", "42 Demo Avenue, Baku"), width=460)
        description = text_input("Description", row.get("description", "Presentation-ready parking facility"), width=460, multiline=True)
        def save(_):
            payload = {"name": require_text(name, "Lot name"), "address": require_text(address, "Address"), "description": description.value or ""}
            state.client.update("lots", row["lot_id"], payload) if is_edit else state.client.create("lots", payload)
            notify("Parking lot saved.")
            refresh()
        open_dialog("Edit parking lot" if is_edit else "Add parking lot", [name, address, description], save, "Save lot")

    def zone_form(row: dict | None = None):
        row = row or {}
        is_edit = bool(row.get("zone_id"))
        lots = get_all("lots")
        options = {lot["name"]: lot["lot_id"] for lot in lots}
        preferred_lot_id = row.get("lot_id") or state.selected_lot_id
        current_lot = next((name for name, lid in options.items() if preferred_lot_id == lid), next(iter(options), ""))
        lot = select_input("Parking lot", list(options.keys()), current_lot, width=460)
        name = text_input("Zone name", row.get("name", "E Premium"), width=460, helper="Unique within the selected lot.")
        floor = text_input("Floor level", str(row.get("floor_level", 0)), width=220)
        zone_type = select_input("Zone type", SLOT_TYPES, row.get("zone_type", "Standard"), width=220)
        priority = text_input("Optimizer priority", str(row.get("priority_score", 35)), width=220, helper="Lower scores are preferred by the optimizer.")
        def save(_):
            if not options:
                raise ValueError("Create a parking lot before creating zones.")
            payload = {"lot_id": options[lot.value], "name": require_text(name, "Zone name"), "floor_level": read_int(floor, "Floor level", -5, 80), "zone_type": zone_type.value, "priority_score": read_int(priority, "Optimizer priority", 0, 100)}
            state.client.update("zones", row["zone_id"], payload) if is_edit else state.client.create("zones", payload)
            notify("Parking zone saved.")
            refresh()
        open_dialog("Edit parking zone" if is_edit else "Add parking zone", [lot, name, ft.Row([floor, zone_type], spacing=12), priority], save, "Save zone")

    def suggest_slot_code(zone_id: str | None) -> str:
        zones = get_all("zones")
        zone = next((item for item in zones if item.get("zone_id") == zone_id), None)
        raw_name = (zone or {}).get("name") or "Slot"
        prefix = next((char.upper() for char in raw_name if char.isalnum()), "S")
        existing = {slot.get("slot_code") for slot in get_all("slots")}
        for number in range(1, 1000):
            candidate = f"{prefix}-{number:02}"
            if candidate not in existing:
                return candidate
        return f"{prefix}-{datetime.now().strftime('%H%M%S')}"

    def slot_form(row: dict | None = None):
        row = row or {}
        is_edit = bool(row.get("slot_id"))
        zones = get_all("zones")
        options = {f"{zone['lot_name']} / {zone['name']}": zone["zone_id"] for zone in zones}
        preferred_zone_id = row.get("zone_id") or state.selected_zone_id
        current_zone = next((label for label, zid in options.items() if preferred_zone_id == zid), next(iter(options), ""))
        default_zone_id = options.get(current_zone)
        zone = select_input("Zone", list(options.keys()), current_zone, width=460)
        code = text_input("Slot code", row.get("slot_code") or suggest_slot_code(default_zone_id), width=220, helper="Must be globally unique.")
        slot_type = select_input("Slot type", SLOT_TYPES, row.get("slot_type", "Standard"), width=220)
        status = select_input("Initial status" if not is_edit else "Status", SLOT_STATUSES, row.get("status", "Available"), width=220)
        distance = text_input("Distance score", str(row.get("distance_score", 45)), width=220)
        priority = text_input("Priority score", str(row.get("priority_score", 35)), width=220)
        reason = text_input("Override reason", row.get("override_reason") or ("Initial slot setup" if not is_edit else ""), width=460)
        def save(_):
            if not options:
                raise ValueError("Create a zone before creating slots.")
            if not zone.value or zone.value not in options:
                raise ValueError("Select a valid zone before saving the slot.")
            payload = {"zone_id": options[zone.value], "slot_code": require_text(code, "Slot code"), "slot_type": slot_type.value, "status": status.value, "distance_score": read_int(distance, "Distance score", 0, 100), "priority_score": read_int(priority, "Priority score", 0, 100), "override_reason": reason.value or None}
            if is_edit:
                state.client.update("slots", row["slot_id"], payload)
            else:
                state.client.create("slots", payload)
            notify("Parking slot saved.")
            refresh()
        open_dialog("Edit parking slot" if is_edit else "Add parking slot", [zone, ft.Row([code, slot_type], spacing=12), ft.Row([status, priority], spacing=12), distance, reason], save, "Save slot")

    def sensor_form(row: dict | None = None):
        row = row or {}
        is_edit = bool(row.get("sensor_id"))
        slots = get_all("slots")
        options = {"Unassigned": None} | {slot["slot_code"]: slot["slot_id"] for slot in slots}
        current = row.get("slot_code") if row.get("slot_code") else "Unassigned"
        code = text_input("Sensor code", row.get("sensor_code", "SNS-900"), width=460, helper="Hardware code must be unique.")
        sensor_type = text_input("Sensor type", row.get("sensor_type", "Ultrasonic"), width=460)
        slot = select_input("Assigned slot", list(options.keys()), current if current in options else "Unassigned", width=460)
        battery = text_input("Battery level", str(row.get("battery_level", 100)), width=220)
        active = ft.Switch(label="Active sensor", value=bool(row.get("is_active", True)))
        def save(_):
            payload = {"sensor_code": require_text(code, "Sensor code"), "sensor_type": require_text(sensor_type, "Sensor type"), "slot_id": options[slot.value], "is_active": active.value, "battery_level": read_int(battery, "Battery level", 0, 100)}
            state.client.update("sensors", row["sensor_id"], payload) if is_edit else state.client.create("sensors", payload)
            notify("Sensor saved.")
            refresh()
        open_dialog("Edit hardware sensor" if is_edit else "Register hardware sensor", [code, sensor_type, slot, ft.Row([battery, active], spacing=12)], save, "Save sensor")

    def tariff_form(row: dict | None = None):
        row = row or {}
        is_edit = bool(row.get("tariff_id"))
        zones = get_all("zones")
        zone_options = {"Any zone": None} | {f"{zone['lot_name']} / {zone['name']}": zone["zone_id"] for zone in zones}
        current_zone = next((label for label, zid in zone_options.items() if row.get("zone_id") == zid), "Any zone")
        name = text_input("Plan name", row.get("name", "Evening Demo Rate"), width=460)
        hourly = text_input("Hourly rate", str(row.get("hourly_rate", 2.75)), width=220)
        grace = text_input("Grace minutes", str(row.get("grace_minutes", 15)), width=220)
        daily = text_input("Daily maximum", str(row.get("daily_max", 20.0)), width=220)
        vehicle = select_input("Vehicle type", ["Any vehicle"] + VEHICLE_TYPES, row.get("vehicle_type") or "Any vehicle", width=220)
        zone = select_input("Applicable zone", list(zone_options.keys()), current_zone, width=460)
        active = ft.Switch(label="Active tariff plan", value=bool(row.get("is_active", True)))
        def save(_):
            payload = {"name": require_text(name, "Plan name"), "hourly_rate": read_float(hourly, "Hourly rate", 0), "grace_minutes": read_int(grace, "Grace minutes", 0, 240), "daily_max": read_float(daily, "Daily maximum", 0), "vehicle_type": None if vehicle.value == "Any vehicle" else vehicle.value, "zone_id": zone_options[zone.value], "is_active": active.value}
            state.client.update("tariffs", row["tariff_id"], payload) if is_edit else state.client.create("tariffs", payload)
            notify("Tariff plan saved.")
            refresh()
        open_dialog("Edit tariff plan" if is_edit else "Create tariff plan", [name, ft.Row([hourly, grace], spacing=12), ft.Row([daily, vehicle], spacing=12), zone, active], save, "Save tariff")

    def session_form(row: dict | None = None):
        zones = get_all("zones")
        zone_options = {"Any compatible zone": None} | {f"{zone['lot_name']} / {zone['name']}": zone["zone_id"] for zone in zones}
        plate = text_input("Plate number", "10-DEMO-01", width=220, helper="Unique active vehicle constraint is enforced.")
        vehicle_type = select_input("Vehicle type", VEHICLE_TYPES, "Car", width=220)
        owner = text_input("Owner name", "Walk-in driver", width=460)
        zone = select_input("Preferred zone", list(zone_options.keys()), "Any compatible zone", width=460)
        optimizer_box = ft.Container(padding=12, border_radius=14, bgcolor=C.blue_soft, content=ft.Text("The backend optimizer will exclude occupied, reserved, disabled, and maintenance slots, then rank compatible bays by zone, type, priority, and distance.", size=12, color=C.blue_dark))
        def preview(_):
            try:
                result = state.client.optimizer({"vehicle_type": vehicle_type.value, "zone_id": zone_options[zone.value]})
                if result.get("slot"):
                    slot = result["slot"]
                    optimizer_box.content = ft.Text(f"Recommended: {slot.get('slot_code')} in {slot.get('zone_name')} · score {result.get('score_breakdown', {}).get('total_score', 'n/a')}", size=12, color=C.blue_dark, weight=ft.FontWeight.W_700)
                else:
                    optimizer_box.content = ft.Text("No compatible slot is currently available.", size=12, color=C.red)
                page.update()
            except Exception as ex:
                notify(str(ex), True)
        def save(_):
            payload = {"plate_number": require_text(plate, "Plate number"), "vehicle_type": vehicle_type.value, "owner_name": owner.value or "", "zone_id": zone_options[zone.value], "use_optimizer": True}
            result = state.client.post("/sessions/start", payload)
            notify(f"Session started in slot {result.get('slot_code')}.")
            refresh()
        open_dialog("Manual session entry with optimized slot", [ft.Row([plate, vehicle_type], spacing=12), owner, zone, optimizer_box, secondary_button("Preview optimized slot", ft.Icons.ONLINE_PREDICTION, preview)], save, "Start session")

    def exit_session_form(row: dict):
        def save(_):
            result = state.client.post(f"/sessions/{row['session_id']}/exit", {})
            notify(f"Session exited. Fee calculated: {money(result.get('fee_amount'))}.")
            refresh()
        open_dialog("Exit session", [ft.Text(f"Vehicle {row.get('plate_number')} will exit from slot {row.get('slot_code')}.", color=C.ink), ft.Container(padding=12, border_radius=14, bgcolor=C.amber_soft, content=ft.Text("The backend will calculate the fee using the tariff snapshot stored at entry time.", size=12, color=C.amber))], save, "Exit and calculate")

    def cancel_session(row: dict):
        state.client.post(f"/sessions/{row['session_id']}/cancel", {})
        notify("Session cancelled and slot released.")
        refresh()

    def emergency_exit_form():
        active = get_all("sessions", status_filter="Active")
        if not active:
            open_dialog("Emergency exit", [empty_state("No active sessions", "There is no vehicle to release right now.", ft.Icons.CHECK_CIRCLE)], None)
            return
        options = {f"{row['plate_number']} · {row['slot_code']} · {compact_time(row['entry_time'])}": row for row in active}
        choice = select_input("Active session", list(options.keys()), width=460)
        def save(_):
            row = options[choice.value]
            result = state.client.post(f"/sessions/{row['session_id']}/exit", {})
            notify(f"Emergency exit completed. Fee: {money(result.get('fee_amount'))}.")
            refresh()
        open_dialog("Emergency exit", [choice, ft.Container(padding=12, border_radius=14, bgcolor=C.red_soft, content=ft.Text("Use this only when an operator must force a vehicle exit from the dashboard.", size=12, color=C.red))], save, "Exit session", destructive=True)

    def payment_form(row: dict):
        amount = text_input("Payment amount", str(row.get("fee_amount", 0)), width=220, helper="Paid payments must match the calculated fee exactly.")
        method = select_input("Payment method", PAYMENT_METHODS, "Card", width=220)
        status = select_input("Payment status", ["Paid", "Pending", "Failed", "Refunded"], "Paid", width=220)
        receipt_preview = ft.Container(padding=14, border_radius=16, bgcolor=C.soft, content=ft.Column([ft.Text("Receipt preview", weight=ft.FontWeight.W_800, color=C.ink), ft.Text(f"Plate: {row.get('plate_number')}"), ft.Text(f"Slot: {row.get('slot_code')}"), ft.Text(f"Calculated fee: {money(row.get('fee_amount'))}"), ft.Text(f"Entry: {compact_time(row.get('entry_time'))}"), ft.Text(f"Exit: {compact_time(row.get('exit_time'))}")], spacing=4))
        def save(_):
            payload = {"session_id": row["session_id"], "paid_amount": read_float(amount, "Payment amount", 0), "method": method.value, "status": status.value}
            state.client.post("/payments/process", payload)
            notify("Payment processed.")
            receipt_modal(row["session_id"])
        open_dialog("Process session payment", [ft.Row([amount, method], spacing=12), status, receipt_preview], save, "Complete payment")

    def receipt_modal(session_id: str | None):
        if not session_id:
            return
        data = state.client.receipt(session_id)
        rows = [
            ("Reference", data.get("reference_number") or "Pending"),
            ("Plate", data.get("plate_number")),
            ("Vehicle", data.get("vehicle_type")),
            ("Slot", data.get("slot_code")),
            ("Entry", compact_time(data.get("entry_time"))),
            ("Exit", compact_time(data.get("exit_time"))),
            ("Fee", money(data.get("fee_amount"))),
            ("Paid", money(data.get("paid_amount") or 0)),
            ("Method", data.get("method") or "Unpaid"),
            ("Status", data.get("status") or "Unpaid"),
        ]
        receipt = ft.Container(width=380, padding=18, border_radius=18, bgcolor=C.panel, border=ft.border.all(1, C.line), content=ft.Column([ft.Row([ft.Icon(ft.Icons.LOCAL_PARKING, color=C.blue), ft.Text("SMARTPARK RECEIPT", weight=ft.FontWeight.W_900, color=C.ink)]), ft.Divider(color=C.line), *[ft.Row([ft.Text(k, color=C.muted, width=110), ft.Text(str(v or ""), color=C.ink, weight=ft.FontWeight.W_600, expand=True)]) for k, v in rows], ft.Divider(color=C.line), ft.Text("Thank you for using SmartPark.", size=11, color=C.muted, text_align=ft.TextAlign.CENTER)], spacing=7))
        open_dialog("Receipt view", [receipt], None, width=420)

    def bulk_slots_form():
        zones = get_all("zones")
        options = {f"{zone['lot_name']} / {zone['name']}": zone["zone_id"] for zone in zones}
        zone = select_input("Zone", list(options.keys()), width=460)
        prefix = text_input("Slot prefix", "E", width=140)
        start = text_input("Start number", "1", width=140)
        end = text_input("End number", "8", width=140)
        slot_type = select_input("Slot type", SLOT_TYPES, "Standard", width=220)
        preview_holder = ft.Column(spacing=8)
        payload_cache = {"value": None, "duplicates": None}
        def make_payload():
            start_num = read_int(start, "Start number", 1, 9999)
            end_num = read_int(end, "End number", start_num, 9999)
            count = end_num - start_num + 1
            return {"zone_id": options[zone.value], "prefix": require_text(prefix, "Slot prefix"), "start_number": start_num, "count": count, "slot_type": slot_type.value, "distance_score": 45, "priority_score": 40}
        def preview(_):
            payload = make_payload()
            result = state.client.bulk_preview(payload)
            payload_cache["value"] = payload
            payload_cache["duplicates"] = result.get("duplicates", 0)
            rows = result.get("rows", [])
            preview_holder.controls = [ft.Text(f"Preview: {result.get('total_requested')} requested · {result.get('duplicates')} duplicates", weight=ft.FontWeight.W_800, color=C.ink), ft.Container(height=210, content=ft.Column([ft.Container(padding=8, border_radius=10, bgcolor=C.red_soft if row.get("issue") else C.green_soft, content=ft.Row([ft.Text(row.get("slot_code"), weight=ft.FontWeight.W_700, color=C.ink), ft.Container(expand=True), ft.Text(row.get("issue") or "Will create", size=11, color=C.red if row.get("issue") else C.green)])) for row in rows], spacing=6, scroll=ft.ScrollMode.AUTO))]
            page.update()
            return False
        def save(_):
            payload = payload_cache["value"] or make_payload()
            if payload_cache.get("duplicates"):
                raise ValueError("Preview contains duplicate slot codes. Change the prefix/range before importing.")
            state.client.bulk_create(payload)
            notify("Bulk slot creation completed.")
            refresh()
        open_dialog("Bulk import infrastructure", [zone, ft.Row([prefix, start, end], spacing=12), slot_type, secondary_button("Preview generated slots", ft.Icons.SEARCH, preview), preview_holder], save, "Confirm import", width=560)

    def assign_sensor_form(slot_id: str):
        sensors = get_all("sensors")
        available = [sensor for sensor in sensors if not sensor.get("slot_id") or sensor.get("slot_id") == slot_id]
        if not available:
            open_dialog("Assign sensor", [empty_state("No available sensors", "Register a hardware sensor first, or unassign one from another slot.", ft.Icons.SENSORS_OFF)], None)
            return
        options = {f"{sensor['sensor_code']} · {sensor.get('slot_code') or 'unassigned'}": sensor for sensor in available}
        choice = select_input("Sensor", list(options.keys()), width=460)
        def save(_):
            sensor = options[choice.value]
            state.client.update("sensors", sensor["sensor_id"], {"slot_id": slot_id, "sensor_code": sensor["sensor_code"], "sensor_type": sensor["sensor_type"], "is_active": bool(sensor["is_active"]), "battery_level": sensor["battery_level"]})
            notify("Sensor assigned to slot.")
            refresh()
        open_dialog("Assign sensor to slot", [choice], save, "Assign sensor")

    def simulate_sensor_form(row: dict):
        status = select_input("Reported status", SENSOR_STATES, "Occupied", width=280)
        raw = text_input("Raw payload note", "manual operator simulation", width=460)
        def save(_):
            state.client.post(f"/sensors/{row['sensor_id']}/simulate", {"reported_status": status.value, "raw_payload": raw.value or "manual operator simulation"})
            notify("Sensor simulation accepted.")
            refresh()
        open_dialog("Simulate sensor update", [ft.Text(f"Sensor {row.get('sensor_code')} assigned to {row.get('slot_code') or 'no slot'}", color=C.muted), status, raw], save, "Simulate")

    def simulate_sensor_action(sensor: dict, status: str):
        try:
            state.client.post(f"/sensors/{sensor['sensor_id']}/simulate", {"reported_status": status, "raw_payload": "slot drawer quick simulation"})
            notify(f"Sensor simulated as {status}.")
            refresh()
        except Exception as ex:
            notify(str(ex), True)

    def export_report_modal():
        kind = select_input("Export type", ["summary", "payments", "sessions"], "summary", width=220)
        csv_box = ft.TextField(label="Generated CSV", multiline=True, min_lines=12, max_lines=16, read_only=True, value="Choose an export type and generate a backend CSV snapshot.", border_radius=12, width=680)
        def generate(_):
            try:
                csv_box.value = state.client.export_csv(kind.value)
                notify(f"{kind.value.title()} CSV generated from the backend.")
                page.update()
            except Exception as ex:
                notify(str(ex), True)
            return False
        open_dialog("Export report", [ft.Row([kind, secondary_button("Generate CSV", ft.Icons.FILE_DOWNLOAD, generate)], spacing=12), csv_box, ft.Text("Local demo export: the CSV is generated by FastAPI and displayed here for copying into a file during presentation.", size=12, color=C.muted)], None, width=720)

    def delete_resource(resource: str, record_id: str):
        state.client.delete(resource, record_id)
        notify("Record deleted.")
        refresh()

    def logout():
        state.logout()
        refresh()

    refresh()
