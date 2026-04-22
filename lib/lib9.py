import flet as ft
page=None

# Container is the basic wrapper box. You use it to give something padding, background color, rounded corners, alignment, or a border. Think of it as the “put this inside a styled box” control.

ft.Container(
    content=ft.Text("Hello"),
    padding=20,
    bgcolor="blue",
    border_radius=10,
)

# DataTable is for showing structured row-and-column data. It is built from DataColumn, DataRow, and DataCell.

ft.DataTable(
    columns=[
        ft.DataColumn(label=ft.Text("Name")),
        ft.DataColumn(label=ft.Text("Age")),
    ],
    rows=[
        ft.DataRow(cells=[ft.DataCell(ft.Text("Ali")), ft.DataCell(ft.Text("19"))]),
    ],
)

# AppBar is the top bar of the app. It usually holds the title and action buttons like search, settings, or theme toggle.

page.appbar = ft.AppBar(
    title=ft.Text("My App"),
    actions=[ft.IconButton(ft.Icons.SETTINGS)],
)

# BottomAppBar is a bar fixed at the bottom, usually for quick actions. In Flet, you assign it to page.bottom_appbar.

page.bottom_appbar = ft.BottomAppBar(
    content=ft.Row([ft.Text("Bottom bar")]),
)

# MenuBar is the classic desktop-style menu strip like File, Edit, Help. It uses SubmenuButton and MenuItemButton.

ft.MenuBar(
    controls=[
        ft.SubmenuButton(
            content=ft.Text("File"),
            controls=[
                ft.MenuItemButton(content=ft.Text("Open")),
            ],
        )
    ]
)

# For Button, Flet has a base Button control, and also common variants like TextButton, FilledButton, and ElevatedButton. The base button supports text, icon, and click behavior.

# Basic button:

ft.Button(content="Click me")

# Button with icon:

ft.Button(content="Car", icon=ft.Icons.DIRECTIONS_CAR)

# Button with click event:

ft.Button(content="Press", on_click=lambda e: print("clicked"))

# Elevated button:

ft.ElevatedButton("Save", on_click=lambda e: print("saved"))

# BottomSheet is a modal panel that slides up from the bottom and shows extra actions or content. It blocks the rest of the app while open.

sheet = ft.BottomSheet(
    content=ft.Container(
        content=ft.Text("Hello from sheet"),
        padding=20,
    )
)
page.show_dialog(sheet)

# SnackBar is a small temporary message, usually for feedback like “Saved” or “Deleted”.

page.show_dialog(
    ft.SnackBar(content=ft.Text("Saved successfully"))
)

# NavigationBar is the bottom navigation for switching between the main sections of an app. It is assigned to page.navigation_bar.

page.navigation_bar = ft.NavigationBar(
    destinations=[
        ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
        ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profile"),
    ]
)

# One important practical note: AppBar, BottomAppBar, and NavigationBar are page-level controls, so you usually set them on page, while Container, DataTable, MenuBar, and buttons go inside your layouts and views.