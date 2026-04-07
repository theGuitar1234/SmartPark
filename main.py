import flet


def form_submit_function(e):
    pass

form_submitted = flet.Text("", size=24, weight=flet.FontWeight.W_600, color="green")
form_container = flet.Container(
    flet.Column(
        [
            flet.Text("Sign Up", size=24, color="black", weight="w600"),
            flet.TextField(
                label="First Name",
                text_size=16,
                border_radius=14,
                color="black",
                focused_border_color="#0a5ff",
                border_width=0.6,
                border_color="black",
            ),
            flet.TextField(
                label="Email",
                text_size=16,
                border_radius=14,
                color="black",
                focused_border_color="#0a5ff",
                border_width=0.6,
                border_color="black",
            ),
            flet.TextField(
                label="Password",
                password=True,
                can_reveal_password=True,
                text_size=16,
                border_radius=14,
                focused_border_color="#0a5ff",
                border_width=0.6,
                border_color="black",
                color="black",
            ),
            flet.Button(
                "Submit",
                color="white",
                width=700,
                height=40,
                style=flet.ButtonStyle(
                    text_style=flet.TextStyle(size=16, weight="w600"), bgcolor="#0a85ff"
                ),
                on_click=form_submit_function,
            ),
            form_submitted,
        ],
        horizontal_alignment="center",
        spacing=20,
    ),
    width=400,
    height=400,
    bgcolor="white",
    border_radius=18,
    padding=20,
)

def signup_view_content(page):
    def form_submit_function(e):
        form_submitted.value = "form submitted!"
        page.go("/success")

    return form_container


def main(page: flet.Page):
    def route_change(e):
        root_signup_view = flet.View(route="/", controls=[signup_view_content(page)])
        success_view = flet.View(route="/success", controls=[flet.Text("Form submitted!")])

        page.views.clear()
        page.views.append(root_signup_view)
        if page.route == "/success":
            page.views.append(success_view)
        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    def toggle_theme(e):
        page.theme_mode = (
            flet.ThemeMode.DARK
            if page.theme_mode == flet.ThemeMode.LIGHT
            else flet.ThemeMode.LIGHT
        )
        page.update()
    
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

    page.views.clear()
    page.views.append(
        flet.View(
            route="/",
            controls=[signup_view_content(page)]
        )
    )
    page.go(page.route)


flet.app(main)
