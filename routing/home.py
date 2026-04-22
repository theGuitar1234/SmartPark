from flet import *
from flet_route import Params, Basket


def home(page: Page, params: Params, basket: Basket):
    input_login = TextField(label="input password")

    def login_button(e):
        page.session.store.set("session_login", input_login.value)
        page.go("/dashboard")
        page.update()

    return View(
        "/",
        [
            Column(
                [
                    Text("Home", size=30),
                ]
            )
        ],
    )
