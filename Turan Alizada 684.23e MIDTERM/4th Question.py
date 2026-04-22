import flet as ft


def main(page: ft.Page):
    page.title = "E-Health Smart Card"
    
    card_id = ft.TextField(label="Card ID")
    issue_date = ft.TextField(label="Issue Date")
    patient_id = ft.TextField(label="Patient ID")
    discount = ft.TextField(label="Discount")
    
    
    success_text = ft.Text(color="green")
    
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Card ID")),
            ft.DataColumn(ft.Text("Issue Date")),
            ft.DataColumn(ft.Text("Patient ID")),
            ft.DataColumn(ft.Text("Discount")),
        ],
    )
    
    page.appbar = ft.AppBar(
        title=ft.Text("E-Health Smart Card"),
        center_title=True,
        actions=[
            ft.ElevatedButton(
                "Service Booking ➜",
                bgcolor="blue",
                color="white",
            ),
        ],
    )

    page.add(
        ft.Column(
            [
                ft.Text("SmartCards", size=24, weight="bold"),
                table,

                ft.Divider(),

                ft.Text("Add New Record", size=20, weight="bold"),

                card_id,
                issue_date,
                patient_id,
                discount,

                ft.ElevatedButton("Add New Record"),

                success_text,
            ],
            expand=True,
        )
    )
    
    page.show_dialog(
        ft.SnackBar(content=ft.Text("Saved successfully"))
    )

    page.bottom_appbar = ft.BottomAppBar(
        content=ft.Row(
            [ft.Text("CRUD TABLE: SmartCards")],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

    page.add(
        ft.Row(
            [
                ft.ElevatedButton("AppBar + Back"),
                ft.ElevatedButton("DataTable"),
                ft.ElevatedButton("TextFields"),
                 ft.ElevatedButton("ElevatedButton + SnackBar"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

ft.run(main)
