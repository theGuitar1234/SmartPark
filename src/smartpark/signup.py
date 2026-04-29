from .lib import ft

from .api_client import APIError, register_user

from .db import *
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
            register_user(name, email, password)

            status_text.value = "Registration successful. You can log in now."
            status_text.color = "green"
            page.update()

            page.go("/login")

        except APIError as ex:
            status_text.value = str(ex)
            status_text.color = "red"
            page.update()
