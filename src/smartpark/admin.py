from .lib import ft

from .db import *
from .dialog import *

from .api_client import APIError, get_dashboard, update_user as api_update_user
from .dialog import show_dialog, close_dialog


def admin_dashboard_view(page: ft.Page, user_state):
    user = user_state.get("current_user")

    if not user:
        return ft.View(route="/dashboard", controls=[])

    try:
        dashboard = get_dashboard()
    except APIError:
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

    def show_snack(message):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message),
                show_close_icon=True,
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

    def open_edit_dialog(e):
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
                updated_user = api_update_user(
                    user_id=current_user["user_id"],
                    full_name=full_name,
                    email=email,
                    new_password=new_password if new_password else None,
                )

                user_state["current_user"] = updated_user

                close_dialog(page, dialog)
                page.go("/dashboard")
                # page.go("/dashboard")

            except APIError as ex:
                result_text.value = str(ex)
                result_text.color = "red"
                page.update()
            except Exception as ex:
                result_text.value = f"Update failed: {ex}"
                result_text.color = "red"
                page.update()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=cancel_click),
            ft.ElevatedButton("Save", on_click=save_changes),
        ]

        show_dialog(page, dialog)

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
                        on_click=open_edit_dialog,
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
                        ft.ElevatedButton("Edit Profile", on_click=open_edit_dialog),
                    ],
                    spacing=12,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
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
            ],
            spacing=20,
            expand=True,
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
