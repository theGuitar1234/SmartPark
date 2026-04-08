import flet as ft
import db
import sqlite3

def show_dialog(page: ft.Page, dialog: ft.AlertDialog):
    page.show_dialog(dialog)


def close_dialog(page: ft.Page, dialog: ft.AlertDialog):
    page.pop_dialog()


def signup_view_content(page: ft.Page):
    status_text = ft.Text("", size=14, color="red")

    first_name_field = ft.TextField(
        label="Full Name",
        width=380,
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.8,
        border_color="black",
    )

    email_field = ft.TextField(
        label="Email",
        width=380,
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.8,
        border_color="black",
    )

    password_field = ft.TextField(
        label="Password",
        width=380,
        password=True,
        can_reveal_password=True,
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.8,
        border_color="black",
    )

    def form_submit_function(e):
        name = first_name_field.value.strip()
        email = email_field.value.strip().lower()
        password = password_field.value

        if not name or not email or not password:
            status_text.value = "Please fill in all fields."
            status_text.color = "red"
            page.update()
            return

        try:
            db.create_user(name, email, password)
            status_text.value = "Registration successful. You can log in now."
            status_text.color = "green"
            page.update()
            page.go("/login")
        except sqlite3.IntegrityError:
            status_text.value = "Email already exists."
            status_text.color = "red"
            page.update()
        except Exception as ex:
            status_text.value = f"Database error: {ex}"
            status_text.color = "red"
            page.update()

    return ft.Container(
        width=460,
        bgcolor="white",
        border_radius=18,
        padding=30,
        content=ft.Column(
            [
                ft.Text(
                    "Sign Up",
                    size=28,
                    color="black",
                    weight=ft.FontWeight.W_600,
                ),
                first_name_field,
                email_field,
                password_field,
                ft.ElevatedButton(
                    "Submit",
                    width=380,
                    height=46,
                    bgcolor="#0A85FF",
                    color="white",
                    on_click=form_submit_function,
                ),
                status_text,
                ft.TextButton("Back to home", on_click=lambda e: page.go("/")),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=18,
            tight=True,
        ),
    )


def login_view_content(page: ft.Page, user_state):
    status_text = ft.Text("", size=14, color="red")

    email_field = ft.TextField(
        label="Email",
        width=380,
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.8,
        border_color="black",
    )

    password_field = ft.TextField(
        label="Password",
        width=380,
        password=True,
        can_reveal_password=True,
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.8,
        border_color="black",
    )

    def form_submit_function(e):
        email = email_field.value.strip().lower()
        password = password_field.value

        if not email or not password:
            status_text.value = "Please fill in all fields."
            status_text.color = "red"
            page.update()
            return

        try:
            user = db.authenticate_user(email, password)

            if user:
                user_state["current_user"] = user
                status_text.value = "User logged in."
                status_text.color = "green"
                page.update()
                page.go("/dashboard")
            else:
                status_text.value = "Invalid email or password."
                status_text.color = "red"
                page.update()

        except Exception as ex:
            status_text.value = f"Database error: {ex}"
            status_text.color = "red"
            page.update()

    return ft.Container(
        width=460,
        bgcolor="white",
        border_radius=18,
        padding=30,
        content=ft.Column(
            [
                ft.Text(
                    "Login",
                    size=28,
                    color="black",
                    weight=ft.FontWeight.W_600,
                ),
                email_field,
                password_field,
                ft.ElevatedButton(
                    "Login",
                    width=380,
                    height=46,
                    bgcolor="#0A85FF",
                    color="white",
                    on_click=form_submit_function,
                ),
                status_text,
                ft.TextButton("Back to home", on_click=lambda e: page.go("/")),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=18,
            tight=True,
        ),
    )


def admin_dashboard_view(page: ft.Page, user_state):
    user = user_state.get("current_user")

    if not user:
        return ft.View(route="/dashboard", controls=[])

    def logout_user(e):
        user_state["current_user"] = None
        page.go("/")

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
                db.update_user(
                    user_id=current_user["user_id"],
                    full_name=full_name,
                    email=email,
                    new_password=new_password if new_password else None,
                )

                user_state["current_user"]["full_name"] = full_name
                user_state["current_user"]["email"] = email

                logout_user(e)
                close_dialog(page, dialog)
                # page.go("/dashboard")

            except sqlite3.IntegrityError:
                result_text.value = "That email already exists."
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
        content=ft.Column([], expand=True),
    )

    layout = ft.Row(
        [
            sidebar,
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column(
                    [
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

def main(page: ft.Page):
    db.init_db()

    user_state = {"current_user": None}

    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()

    def route_change(e):
        if page.route == "/dashboard" and not user_state["current_user"]:
            page.go("/login")
            return

        home_view = ft.View(
            route="/",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=420,
                    bgcolor="white",
                    border_radius=18,
                    padding=30,
                    content=ft.Column(
                        [
                            ft.Text(
                                "Welcome",
                                size=30,
                                weight=ft.FontWeight.W_600,
                                color="black",
                            ),
                            ft.ElevatedButton(
                                "Create account",
                                width=300,
                                on_click=lambda e: page.go("/register"),
                            ),
                            ft.ElevatedButton(
                                "Login",
                                width=300,
                                on_click=lambda e: page.go("/login"),
                            ),
                            ft.TextButton(
                                "Toggle theme",
                                on_click=toggle_theme,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                    ),
                )
            ],
        )

        register_view = ft.View(
            route="/register",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[signup_view_content(page)],
        )

        login_view = ft.View(
            route="/login",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[login_view_content(page, user_state)],
        )

        dashboard_view = admin_dashboard_view(page, user_state)

        page.views.clear()

        if page.route == "/":
            page.views.append(home_view)
        elif page.route == "/register":
            page.views.append(home_view)
            page.views.append(register_view)
        elif page.route == "/login":
            page.views.append(home_view)
            page.views.append(login_view)
        elif page.route == "/dashboard":
            page.views.append(dashboard_view)
        else:
            page.views.append(home_view)

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            page.go("/")

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.title = "SmartPark"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#EDEFF2"
    page.padding = 0

    page.window.width = 1280
    page.window.height = 820
    page.window.min_width = 1000
    page.window.min_height = 700

    # page.go("/")
    route_change(None)


ft.app(target=main)