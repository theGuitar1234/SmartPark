from __future__ import annotations

import os
import flet as ft

from .frontend.app import main


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
