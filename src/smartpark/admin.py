import math

from .lib import ft

from .api_client import (
    create_item as api_create_item,
    delete_item as api_delete_item,
    get_items as api_get_items,
    update_item as api_update_item,
)
from .db import get_dashboard_data, update_user
from .dialog import show_dialog, close_dialog


def admin_dashboard_view(page: ft.Page, user_state):
    user = user_state.get("current_user")

    if not user:
        return ft.View(route="/dashboard", controls=[])

    try:
        dashboard = get_dashboard_data()
    except Exception:
        dashboard = {
            "total_slots": 0,
            "occupied": 0,
            "available": 0,
            "reserved": 0,
            "slots": [],
        }

    def logout_user(e):
        user_state["current_user"] = None
        page.go("/")

    def show_snack(message, bgcolor=None):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message),
                show_close_icon=True,
                bgcolor=bgcolor,
            )
        )

    def open_quick_actions_sheet(e):
        sheet = ft.BottomSheet(
            show_drag_handle=True,
            content=ft.Container(
                padding=20,
                content=ft.Column(
                    [
                        ft.Text("Quick actions", size=18, weight=ft.FontWeight.W_600),
                        ft.Button(
                            "Show welcome message",
                            on_click=lambda e: show_snack("Welcome back"),
                        ),
                        ft.Button("Close", on_click=lambda e: page.pop_dialog()),
                    ],
                    tight=True,
                ),
            ),
        )
        page.show_dialog(sheet)

    def open_edit_profile_dialog(e):
        current_user = user_state["current_user"]

        name_field = ft.TextField(
            label="Full Name",
            value=current_user["full_name"],
            width=360,
        )

        email_field = ft.TextField(
            label="Email",
            value=current_user["email"],
            width=360,
        )

        password_field = ft.TextField(
            label="New Password",
            password=True,
            can_reveal_password=True,
            width=360,
        )

        result_text = ft.Text("", size=14, color="red")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit User Details"),
            content=ft.Container(
                width=380,
                content=ft.Column(
                    [
                        name_field,
                        email_field,
                        password_field,
                        result_text,
                    ],
                    spacing=12,
                    tight=True,
                ),
            ),
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def cancel_click(e):
            close_dialog(page, dialog)

        def save_changes(e):
            full_name = name_field.value.strip()
            email = email_field.value.strip().lower()
            new_password = password_field.value.strip()

            if not full_name or not email:
                result_text.value = "Name and email are required."
                result_text.color = "red"
                page.update()
                return

            try:
                updated_user = update_user(
                    user_id=current_user["user_id"],
                    full_name=full_name,
                    email=email,
                    new_password=new_password if new_password else None,
                )

                user_state["current_user"] = updated_user

                close_dialog(page, dialog)
                page.go("/dashboard")

            except Exception as ex:
                result_text.value = f"Update failed: {ex}"
                result_text.color = "red"
                page.update()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=cancel_click),
            ft.ElevatedButton("Save", on_click=save_changes),
        ]

        show_dialog(page, dialog)

    current_page = [1]
    total_pages = [1]
    page_size = [10]

    search_field = ft.TextField(
        label="Search Field1 / Field2 / Field3",
        width=320,
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda e: go_to_page(1),
    )

    sort_dropdown = ft.Dropdown(
        label="Sort by",
        width=160,
        value="id",
        options=[
            ft.dropdown.Option("id", "ID"),
            ft.dropdown.Option("field1", "Field1"),
            ft.dropdown.Option("field2", "Field2"),
            ft.dropdown.Option("field3", "Field3"),
        ],
    )

    order_dropdown = ft.Dropdown(
        label="Order",
        width=150,
        value="asc",
        options=[
            ft.dropdown.Option("asc", "Ascending"),
            ft.dropdown.Option("desc", "Descending"),
        ],
    )

    rows_dropdown = ft.Dropdown(
        label="Rows",
        width=120,
        value="10",
        options=[
            ft.dropdown.Option("10", "10"),
            ft.dropdown.Option("25", "25"),
            ft.dropdown.Option("50", "50"),
        ],
    )

    sort_dropdown.on_select = lambda e: go_to_page(1)
    order_dropdown.on_select = lambda e: go_to_page(1)
    rows_dropdown.on_select = lambda e: change_page_size()

    counter_text = ft.Text("", size=13, color="black54")
    pager_row = ft.Row([], alignment=ft.MainAxisAlignment.CENTER, wrap=True)

    new_field1 = ft.TextField(label="Field1", width=220)
    new_field2 = ft.TextField(label="Field2", width=220)
    new_field3 = ft.TextField(label="Field3", width=220)

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Field1")),
            ft.DataColumn(ft.Text("Field2")),
            ft.DataColumn(ft.Text("Field3")),
            ft.DataColumn(ft.Text("Actions")),
        ],
        rows=[],
    )

    dlg_id = ft.TextField(label="ID", width=300, read_only=True)
    dlg_field1 = ft.TextField(label="Field1", width=300)
    dlg_field2 = ft.TextField(label="Field2", width=300)
    dlg_field3 = ft.TextField(label="Field3", width=300)

    def close_item_dialog(e):
        close_dialog(page, edit_dialog)

    def save_edit(e):
        payload = {
            "id": dlg_id.value,
            "field1": dlg_field1.value.strip(),
            "field2": dlg_field2.value.strip(),
            "field3": dlg_field3.value.strip(),
        }

        try:
            api_update_item(
                int(dlg_id.value),
                payload["field1"],
                payload["field2"],
                payload["field3"],
            )
            close_dialog(page, edit_dialog)
            show_snack("Record updated!", ft.Colors.GREEN_600)
            load_table()
        except Exception as ex:
            show_snack(str(ex), ft.Colors.RED_600)

    edit_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Edit Record"),
        content=ft.Column(
            [dlg_id, dlg_field1, dlg_field2, dlg_field3],
            tight=True,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=close_item_dialog),
            ft.ElevatedButton(
                "Save",
                bgcolor="#1565c0",
                color=ft.Colors.WHITE,
                on_click=save_edit,
            ),
        ],
    )

    def open_edit_dialog(row_data: dict):
        dlg_id.value = str(row_data["id"])
        dlg_field1.value = row_data["field1"]
        dlg_field2.value = row_data["field2"]
        dlg_field3.value = row_data["field3"]
        show_dialog(page, edit_dialog)

    def create_record(e):
        try:
            api_create_item(
                new_field1.value.strip(),
                new_field2.value.strip(),
                new_field3.value.strip(),
            )
            new_field1.value = ""
            new_field2.value = ""
            new_field3.value = ""
            show_snack("Record created!", ft.Colors.GREEN_600)
            go_to_page(1)
        except Exception as ex:
            show_snack(str(ex), ft.Colors.RED_600)

    def make_delete(iid: int):
        def on_delete(e):
            try:
                api_delete_item(iid)
                show_snack(f"Deleted: {iid}", ft.Colors.GREEN_600)
                load_table()
            except Exception as ex:
                show_snack(str(ex), ft.Colors.RED_600)

        return on_delete

    def make_edit(row_data: dict):
        def on_edit(e):
            open_edit_dialog(row_data)

        return on_edit

    def _page_btn(page_number: int, current: int):
        return ft.ElevatedButton(
            str(page_number),
            bgcolor="#1565c0" if page_number == current else None,
            color=ft.Colors.WHITE if page_number == current else None,
            width=42,
            on_click=lambda e, pg=page_number: go_to_page(pg),
        )

    def rebuild_pager():
        pager_row.controls.clear()
        tp = total_pages[0]
        cp = current_page[0]

        pager_row.controls.append(
            ft.IconButton(
                ft.Icons.CHEVRON_LEFT,
                tooltip="Previous",
                disabled=(cp <= 1),
                on_click=lambda e: go_to_page(cp - 1),
            )
        )

        start_p = max(1, cp - 3)
        end_p = min(tp, start_p + 6)
        start_p = max(1, end_p - 6)

        if start_p > 1:
            pager_row.controls.append(_page_btn(1, cp))
            if start_p > 2:
                pager_row.controls.append(ft.Text("…", size=16))

        for page_number in range(start_p, end_p + 1):
            pager_row.controls.append(_page_btn(page_number, cp))

        if end_p < tp:
            if end_p < tp - 1:
                pager_row.controls.append(ft.Text("…", size=16))
            pager_row.controls.append(_page_btn(tp, cp))

        pager_row.controls.append(
            ft.IconButton(
                ft.Icons.CHEVRON_RIGHT,
                tooltip="Next",
                disabled=(cp >= tp),
                on_click=lambda e: go_to_page(cp + 1),
            )
        )

    def load_table():
        try:
            limit = page_size[0]
            offset = (current_page[0] - 1) * limit
            data = api_get_items(
                search=search_field.value or "",
                limit=limit,
                offset=offset,
                sort_by=sort_dropdown.value or "id",
                order=order_dropdown.value or "asc",
            )

            total = int(data.get("total", 0))
            total_pages[0] = max(1, math.ceil(total / limit))

            if current_page[0] > total_pages[0]:
                current_page[0] = total_pages[0]
                load_table()
                return

            start = offset + 1 if total > 0 else 0
            end = min(offset + limit, total)
            counter_text.value = f"Showing {start}–{end} of {total} records"

            table.rows.clear()
            for item in data.get("items", []):
                item_id = int(item["id"])
                table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(item["id"]))),
                            ft.DataCell(ft.Text(item["field1"])),
                            ft.DataCell(ft.Text(item["field2"])),
                            ft.DataCell(ft.Text(item["field3"])),
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.IconButton(
                                            ft.Icons.EDIT,
                                            tooltip="Edit",
                                            on_click=make_edit(item),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.DELETE,
                                            tooltip="Delete",
                                            icon_color=ft.Colors.RED_400,
                                            on_click=make_delete(item_id),
                                        ),
                                    ]
                                )
                            ),
                        ]
                    )
                )

            rebuild_pager()
            page.update()
        except Exception as ex:
            show_snack(f"Cannot load records: {ex}", ft.Colors.RED_600)

    def go_to_page(n: int):
        current_page[0] = max(1, min(n, total_pages[0]))
        load_table()

    def change_page_size():
        try:
            page_size[0] = int(rows_dropdown.value or "10")
        except ValueError:
            page_size[0] = 10
        go_to_page(1)
    
    def bind_dropdown_event(control, handler):
        if hasattr(control, "on_select"):
            control.on_select = handler
        else:
            control.on_change = handler

    bind_dropdown_event(sort_dropdown, lambda e: go_to_page(1))
    bind_dropdown_event(order_dropdown, lambda e: go_to_page(1))
    bind_dropdown_event(rows_dropdown, lambda e: change_page_size())

    load_table()

    sidebar = ft.Container(
        width=220,
        bgcolor="#F4F5F7",
        padding=20,
        content=ft.Column(
            [
                ft.Text(
                    "SmartPark",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color="#0A85FF",
                ),
                ft.Divider(),
                ft.TextButton("Overview"),
                ft.TextButton("Zones & Slots"),
                ft.TextButton("Sessions"),
                ft.TextButton("Settings"),
                ft.Container(expand=True),
                ft.TextButton("Logout", on_click=logout_user),
            ],
            spacing=10,
            expand=True,
        ),
    )

    menu_bar = ft.MenuBar(
        controls=[
            ft.SubmenuButton(
                content=ft.Text("File"),
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text("Refresh"),
                        on_click=lambda e: show_snack("Dashboard refreshed"),
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Quick actions"),
                        on_click=open_quick_actions_sheet,
                    ),
                ],
            ),
            ft.SubmenuButton(
                content=ft.Text("Account"),
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text("Edit profile"),
                        on_click=open_edit_profile_dialog,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Logout"),
                        on_click=logout_user,
                    ),
                ],
            ),
        ]
    )

    header = ft.Container(
        bgcolor="white",
        border_radius=16,
        padding=20,
        content=ft.Row(
            [
                ft.Text(
                    "Dashboard",
                    size=24,
                    weight=ft.FontWeight.W_600,
                    color="black",
                ),
                ft.Row(
                    [
                        ft.Text(
                            user["full_name"],
                            size=16,
                            weight=ft.FontWeight.W_500,
                            color="black",
                        ),
                        ft.ElevatedButton(
                            "Edit Profile", on_click=open_edit_profile_dialog
                        ),
                    ],
                    spacing=12,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    )

    records_section = ft.Container(
        padding=16,
        border_radius=16,
        bgcolor="#F9FAFB",
        content=ft.Column(
            [
                ft.Text(
                    "Activity #5 Paginated Records", size=20, weight=ft.FontWeight.W_600
                ),
                ft.Text(
                    "Search, sort, paginate, create, edit, and delete records through FastAPI.",
                    size=13,
                    color="black54",
                ),
                ft.Row(
                    [search_field, sort_dropdown, order_dropdown, rows_dropdown],
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                ),
                counter_text,
                ft.Row(
                    [
                        new_field1,
                        new_field2,
                        new_field3,
                        ft.ElevatedButton(
                            "Add Record",
                            icon=ft.Icons.ADD,
                            on_click=create_record,
                        ),
                    ],
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                ),
                ft.Container(height=8),
                ft.Row(scroll=ft.ScrollMode.AUTO, controls=[table]),
                pager_row,
            ],
            spacing=12,
        ),
    )

    main_content = ft.Container(
        expand=True,
        bgcolor="white",
        border_radius=16,
        padding=20,
        width=500,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            width=180,
                            height=100,
                            bgcolor="#EAF4FF",
                            border_radius=16,
                            padding=15,
                            content=ft.Column(
                                [
                                    ft.Text("Total slots", size=14, color="black54"),
                                    ft.Text(
                                        str(dashboard["total_slots"]),
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=6,
                            ),
                        ),
                        ft.Container(
                            width=180,
                            height=100,
                            bgcolor="#E8FFF1",
                            border_radius=16,
                            padding=15,
                            content=ft.Column(
                                [
                                    ft.Text("Occupied", size=14, color="black54"),
                                    ft.Text(
                                        str(dashboard["occupied"]),
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=6,
                            ),
                        ),
                        ft.Container(
                            width=180,
                            height=100,
                            bgcolor="#FFF4E8",
                            border_radius=16,
                            padding=15,
                            content=ft.Column(
                                [
                                    ft.Text("Available", size=14, color="black54"),
                                    ft.Text(
                                        str(dashboard["available"]),
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=6,
                            ),
                        ),
                    ],
                    spacing=15,
                    wrap=True,
                ),
                ft.Row(
                    [
                        ft.TextButton(
                            "Basic button",
                            on_click=lambda e: show_snack("Basic button clicked"),
                        ),
                        ft.OutlinedButton(
                            "With icon",
                            icon=ft.Icons.DIRECTIONS_CAR,
                            on_click=lambda e: show_snack("Icon button clicked"),
                        ),
                        ft.FilledButton(
                            "Click event",
                            on_click=lambda e: show_snack("Click event fired"),
                        ),
                        ft.ElevatedButton(
                            "Open BottomSheet",
                            icon=ft.Icons.KEYBOARD_ARROW_UP,
                            on_click=open_quick_actions_sheet,
                        ),
                    ],
                    spacing=12,
                    wrap=True,
                ),
                ft.Container(
                    padding=10,
                    border_radius=16,
                    bgcolor="#F9FAFB",
                    content=ft.DataTable(
                        columns=[
                            ft.DataColumn(label=ft.Text("Zone")),
                            ft.DataColumn(label=ft.Text("Slot")),
                            ft.DataColumn(label=ft.Text("Status")),
                        ],
                        rows=[
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(slot["zone"])),
                                    ft.DataCell(ft.Text(slot["slot_number"])),
                                    ft.DataCell(ft.Text(slot["status"])),
                                ]
                            )
                            for slot in dashboard["slots"]
                        ],
                    ),
                ),
                ft.Container(height=12),
                records_section,
            ],
            spacing=20,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    layout = ft.Row(
        [
            sidebar,
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
                        menu_bar,
                        header,
                        main_content,
                    ],
                    spacing=20,
                    expand=True,
                ),
            ),
        ],
        expand=True,
    )

    return ft.View(
        route="/dashboard",
        padding=0,
        spacing=0,
        controls=[layout],
    )
