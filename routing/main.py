from flet import *
from flet_route import Routing, path

from home import home

def main(page:Page):
    page.window_width = 300
    
    # Define Routes
    routes = [
        path(url="/", view=home, clear=True),
    ]
    Routing(page=page, app_routes=routes)
    
    page.go("/")

run(main)