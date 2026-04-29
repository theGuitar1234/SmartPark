from lib import ft


def show_dialog(page: ft.Page, dialog: ft.AlertDialog):
    page.show_dialog(dialog)


def close_dialog(page: ft.Page, dialog: ft.AlertDialog):
    page.pop_dialog()
