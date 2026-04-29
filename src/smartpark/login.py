from .lib import ft

from .db import *

from .api_client import APIError, login_user

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
            user = login_user(email, password)

            user_state["current_user"] = user
            status_text.value = "User logged in."
            status_text.color = "green"
            page.update()

            page.go("/dashboard")

        except APIError as ex:
            status_text.value = str(ex)
            status_text.color = "red"
            page.update()