from .lib import ft

from .db import create_user
import sqlite3


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
            create_user(name, email, password)
            status_text.value = "Registration successful. You can log in now."
            status_text.color = "green"
            page.update()
            page.go("/login")
        except sqlite3.IntegrityError:
            status_text.value = "That email already exists."
            status_text.color = "red"
            page.update()
        except ValueError as ex:
            status_text.value = str(ex)
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
                    "Create account",
                    size=30,
                    weight=ft.FontWeight.W_600,
                    color="black",
                ),
                first_name_field,
                email_field,
                password_field,
                ft.ElevatedButton(
                    "Create account",
                    width=300,
                    on_click=form_submit_function,
                ),
                status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
    )
