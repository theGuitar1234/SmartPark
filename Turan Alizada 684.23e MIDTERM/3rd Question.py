import flet as ft


def main(page: ft.Page):
    page.title = "E-Health Smart Card"

    sheet1 = ft.BottomSheet(
        content=ft.Container(
            content=ft.Text("My Card"),
            padding=20,
        ),
    )

    sheet2 = ft.BottomSheet(
        content=ft.Container(
            content=ft.Text("Services"),
            padding=20,
        ),
    )

    sheet3 = ft.BottomSheet(
        content=ft.Container(
            content=ft.Text("Discounts"),
            padding=20,
        ),
    )

    def open_sheet1(e):
        page.show_dialog(sheet1)

    def open_sheet2(e):
        page.show_dialog(sheet2)

    def open_sheet3(e):
        page.show_dialog(sheet3)
        
    page.appbar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.MENU),
        actions=[
            ft.ElevatedButton(
                "Service Booking -> ",
                bgcolor="blue",
                color="white",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
        ],
    )

    page.add(
        ft.Container(
            content=ft.Text("[App content area]", text_align="center"),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
    )

    page.add(
        ft.Row(
            [
                ft.ElevatedButton("My Card", on_click=open_sheet1),
                ft.ElevatedButton("Services", on_click=open_sheet2),
                ft.ElevatedButton("Discounts", on_click=open_sheet3),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

    page.bottom_appbar = ft.BottomAppBar(
        content=ft.Row(
            [
                ft.Text("AppBar: #0069c"),
                ft.Text("Accent: #0097a7")
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    )

ft.run(main)
