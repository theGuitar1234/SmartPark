from lib import ft


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
