from .lib import ft

from .admin import admin_dashboard_view
from .login import login_view_content
from .signup import signup_view_content

from .db import *
from .api_routes import router as api_router
from fastapi import FastAPI


def main(page: ft.Page):
    init_db()

    user_state = {"current_user": None}
    routes = ["/", "/register", "/login"]

    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()

    def handle_nav_change(e):
        page.go(routes[e.control.selected_index])

    def route_change(e):
        if page.route == "/dashboard" and not user_state["current_user"]:
            page.go("/login")
            return

        page.appbar = None
        page.bottom_appbar = None
        page.navigation_bar = None

        if page.route in routes:
            page.navigation_bar = ft.NavigationBar(
                selected_index={"/": 0, "/register": 1, "/login": 2}.get(page.route, 0),
                on_change=handle_nav_change,
                destinations=[
                    ft.NavigationBarDestination(
                        icon=ft.Icons.HOME_OUTLINED, label="Home"
                    ),
                    ft.NavigationBarDestination(
                        icon=ft.Icons.PERSON_ADD_ALT_1, label="Register"
                    ),
                    ft.NavigationBarDestination(icon=ft.Icons.LOGIN, label="Login"),
                ],
            )

        if page.route == "/dashboard":
            page.appbar = ft.AppBar(
                leading=ft.Icon(ft.Icons.LOCAL_PARKING, color=ft.Colors.WHITE),
                leading_width=40,
                title=ft.Text("SmartPark Dashboard"),
                bgcolor="#0A85FF",
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.DARK_MODE_OUTLINED,
                        icon_color=ft.Colors.WHITE,
                        on_click=toggle_theme,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                        icon_color=ft.Colors.WHITE,
                        on_click=lambda e: page.show_dialog(
                            ft.SnackBar(content=ft.Text("Notifications clicked"))
                        ),
                    ),
                ],
            )

            page.bottom_appbar = ft.BottomAppBar(
                bgcolor="#0A85FF",
                content=ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.HOME_OUTLINED,
                            icon_color=ft.Colors.WHITE,
                            on_click=lambda e: page.go("/dashboard"),
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            icon_color=ft.Colors.WHITE,
                            on_click=lambda e: user_state.update({"current_user": None})
                            or page.go("/"),
                        ),
                    ]
                ),
            )

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


# ft.app(target=main, host="localhost", port=8000, view=ft.AppView.WEB_BROWSER)
# app = ft.run(main, export_asgi_app=True)
# app.include_router(api_router)

init_db()

flet_app = ft.run(main, export_asgi_app=True)

app = FastAPI(
    title="SmartPark API",
    description="Backend API for the SmartPark Flet application",
    version="1.0.0",
)

#python -m uvicorn smartpark.main:app --reload --port 8000 --app-dir src
app.include_router(api_router)

app.mount("/", flet_app)
