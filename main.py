import flet
import db
import sqlite3


form_submitted = flet.Text(
    "",
    size=24,
    weight=flet.FontWeight.W_600,
    color="green",
)


def signup_view_content(page):
    def form_submit_function(e):
        name = first_name_field.value.strip()
        email = email_field.value.strip().lower()
        password = password_field.value

        if not name or not email or not password:
            form_submitted.value = "Please fill in all fields."
            form_submitted.color = "red"
            page.update()
            return

        try:
            db.create_user(name, email, password)
            form_submitted.value = "Registration successful!"
            form_submitted.color = "green"
            page.update()
            page.go("/success")
        except sqlite3.IntegrityError:
            form_submitted.value = "Email already exists."
            form_submitted.color = "red"
            page.update()
        except Exception as ex:
            form_submitted.value = f"Database error: {ex}"
            form_submitted.color = "red"
            page.update()

    first_name_field = flet.TextField(
        label="First Name",
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.6,
        border_color="black",
    )

    email_field = flet.TextField(
        label="Email",
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.6,
        border_color="black",
    )

    password_field = flet.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        text_size=16,
        border_radius=14,
        focused_border_color="#0A85FF",
        border_width=0.6,
        border_color="black",
    )

    return flet.Container(
        flet.Column(
            [
                flet.Text(
                    "Sign Up",
                    size=24,
                    color="black",
                    weight=flet.FontWeight.W_600,
                ),
                first_name_field,
                email_field,
                password_field,
                flet.Button(
                    "Submit",
                    color="white",
                    width=350,
                    height=40,
                    style=flet.ButtonStyle(
                        text_style=flet.TextStyle(
                            size=16,
                            weight=flet.FontWeight.W_600,
                        ),
                        bgcolor="#0A85FF",
                    ),
                    on_click=form_submit_function,
                ),
                form_submitted,
                flet.TextButton("Back to home", on_click=lambda e: page.go("/")),
            ],
            horizontal_alignment="center",
            spacing=20,
        ),
        width=400,
        height=420,
        bgcolor="white",
        border_radius=18,
        padding=20,
    )

def login_view_content(page):
    def form_submit_function(e):
        name = first_name_field.value.strip()
        email = email_field.value.strip().lower()
        password = password_field.value

        if not name or not email or not password:
            form_submitted.value = "Please fill in all fields."
            form_submitted.color = "red"
            page.update()
            return

        try:
            db.create_user(name, email, password)
            form_submitted.value = "Registration successful!"
            form_submitted.color = "green"
            page.update()
            page.go("/success")
        except sqlite3.IntegrityError:
            form_submitted.value = "User Logged In!"
            form_submitted.color = "green"
            page.update()
        except Exception as ex:
            form_submitted.value = f"Database error: {ex}"
            form_submitted.color = "red"
            page.update()

    first_name_field = flet.TextField(
        label="First Name",
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.6,
        border_color="black",
    )

    email_field = flet.TextField(
        label="Email",
        text_size=16,
        border_radius=14,
        color="black",
        focused_border_color="#0A85FF",
        border_width=0.6,
        border_color="black",
    )

    password_field = flet.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        text_size=16,
        border_radius=14,
        focused_border_color="#0A85FF",
        border_width=0.6,
        border_color="black",
    )

    return flet.Container(
        flet.Column(
            [
                flet.Text(
                    "Sign Up",
                    size=24,
                    color="black",
                    weight=flet.FontWeight.W_600,
                ),
                first_name_field,
                email_field,
                password_field,
                flet.Button(
                    "Submit",
                    color="white",
                    width=350,
                    height=40,
                    style=flet.ButtonStyle(
                        text_style=flet.TextStyle(
                            size=16,
                            weight=flet.FontWeight.W_600,
                        ),
                        bgcolor="#0A85FF",
                    ),
                    on_click=form_submit_function,
                ),
                form_submitted,
                flet.TextButton("Back to home", on_click=lambda e: page.go("/")),
            ],
            horizontal_alignment="center",
            spacing=20,
        ),
        width=400,
        height=420,
        bgcolor="white",
        border_radius=18,
        padding=20,
    )

def main(page: flet.Page):
    # db.init_db()

    def toggle_theme(e):
        page.theme_mode = (
            flet.ThemeMode.DARK
            if page.theme_mode == flet.ThemeMode.LIGHT
            else flet.ThemeMode.LIGHT
        )
        page.update()

    def route_change(e):
        root_signup_view = flet.View(
            route="/",
            controls=[
                flet.Column(
                    [
                        flet.Text(
                            "Welcome",
                            size=28,
                            weight=flet.FontWeight.W_600,
                        ),
                        flet.TextButton(
                            "Create account",
                            on_click=lambda e: page.go("/register"),
                        ),
                        flet.TextButton(
                            "Login",
                            on_click=lambda e: page.go("/login")
                        ),
                        flet.TextButton(
                            "Toggle theme",
                            on_click=toggle_theme,
                        ),
                    ],
                    horizontal_alignment="center",
                    alignment="center",
                    spacing=20,
                )
            ],
            vertical_alignment="center",
            horizontal_alignment="center",
        )

        register_view = flet.View(
            route="/register",
            controls=[signup_view_content(page)],
            vertical_alignment="center",
            horizontal_alignment="center",
        )
        
        login_view = flet.View(
            route="/login",
            controls=[login_view_content(page)],
            vertical_alignment="center",
            horizontal_alignment="center" 
        )

        success_view = flet.View(
            route="/success",
            controls=[
                flet.Column(
                    [
                        flet.Text(
                            "Registration successful!",
                            size=28,
                            weight=flet.FontWeight.W_600,
                        ),
                        flet.TextButton(
                            "Back to home",
                            on_click=lambda e: page.go("/"),
                        ),
                    ],
                    horizontal_alignment="center",
                    alignment="center",
                    spacing=20,
                )
            ],
            vertical_alignment="center",
            horizontal_alignment="center",
        )

        page.views.clear()
        page.views.append(root_signup_view)

        if page.route == "/register":
            page.views.append(register_view)
        elif page.route == "/success":
            page.views.append(success_view)

        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.theme = flet.Theme()
    page.dark_theme = flet.Theme()
    page.theme_mode = flet.ThemeMode.LIGHT

    page.window.width = 600
    page.window.height = 500
    page.bgcolor = "#e6e6e6"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"

    route_change(None)


flet.app(main)