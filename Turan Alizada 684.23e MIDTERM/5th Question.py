import flet as ft

import os
import sqlite3
import hashlib
import hmac
import re


DB_PATH = "data/ehealth.db"
DATA_DIR = "data"


def get_connection():
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
        CREATE TABLE IF NOT EXISTS records (
            card_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id   INTEGER NOT NULL UNIQUE,
            issuedate    TEXT NOT NULL UNIQUE,
            discount   TEXT NOT NULL,
        );
        """
        )


import flet as ft


def main(page: ft.Page):
    page.title = "E-Health Smart Card"

    def route_change(route):
        page.views.clear()

        if page.route == "/":
            page.views.append(home_view())
        elif page.route == "/table":
            page.views.append(table_view())
        elif page.route == "/services":
            page.views.append(services_view())

        page.update()

    def go(route):
        page.go(route)

    page.on_route_change = route_change

    def home_view():
        return ft.View(
            "/",
            [
                ft.AppBar(title=ft.Text("Home")),
                ft.Column(
                    [
                        ft.Text("Welcome to E-Health App", size=24),
                        ft.ElevatedButton(
                            "Go to SmartCards Table", on_click=lambda e: go("/table")
                        ),
                        ft.ElevatedButton(
                            "Go to Services", on_click=lambda e: go("/services")
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
        )

    def table_view():
        card_id = ft.TextField(label="Card ID")
        issue_date = ft.TextField(label="Issue Date")
        patient_id = ft.TextField(label="Patient ID")
        discount = ft.TextField(label="Discount")

        success_text = ft.Text()

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Card ID")),
                ft.DataColumn(ft.Text("Issue Date")),
                ft.DataColumn(ft.Text("Patient ID")),
                ft.DataColumn(ft.Text("Discount")),
            ],
            rows=[],
        )

        def add_record(e):
            if not card_id.value:
                success_text.value = "Card ID required!"
                success_text.color = "red"
            else:
                table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(card_id.value)),
                            ft.DataCell(ft.Text(issue_date.value)),
                            ft.DataCell(ft.Text(patient_id.value)),
                            ft.DataCell(ft.Text(discount.value)),
                        ]
                    )
                )
                success_text.value = "Added!"
                success_text.color = "green"

                card_id.value = ""
                issue_date.value = ""
                patient_id.value = ""
                discount.value = ""

            page.update()

        return ft.View(
            "/table",
            [
                ft.AppBar(
                    title=ft.Text("SmartCards"),
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: go("/"),
                    ),
                ),
                ft.Column(
                    [
                        table,
                        ft.Divider(),
                        card_id,
                        issue_date,
                        patient_id,
                        discount,
                        ft.ElevatedButton("Add", on_click=add_record),
                        success_text,
                    ]
                ),
            ],
        )

    def services_view():
        sheet = ft.BottomSheet(
            content=ft.Container(
                content=ft.Text("Service Details"),
                padding=20,
            )
        )

        def open_sheet(e):
            page.open(sheet)

        return ft.View(
            "/services",
            [
                ft.AppBar(
                    title=ft.Text("Services"),
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: go("/"),
                    ),
                ),
                ft.Column(
                    [
                        ft.Text("Services Page"),
                        ft.ElevatedButton("Open Bottom Sheet", on_click=open_sheet),
                    ]
                ),
            ],
        )

    # page.go("/")
    route_change(None)


ft.run(main)
