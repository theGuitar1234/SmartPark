from __future__ import annotations

from dataclasses import dataclass

from .api_client import SmartParkClient


@dataclass
class AppState:
    client: SmartParkClient
    token: str | None = None
    user: dict | None = None
    view: str = "Dashboard"
    search_query: str = ""
    global_search_query: str = ""
    slot_search_query: str = ""
    session_search_query: str = ""
    selected_lot_id: str | None = None
    selected_zone_id: str | None = None
    selected_slot_id: str | None = None
    session_filter: str = "All"
    payment_filter: str = "All"

    def login(self, data: dict) -> None:
        self.token = data["token"]
        self.user = data["user"]
        self.client.set_token(self.token)

    def logout(self) -> None:
        self.token = None
        self.user = None
        self.client.set_token(None)
        self.view = "Dashboard"
        self.search_query = ""
        self.global_search_query = ""
        self.slot_search_query = ""
        self.session_search_query = ""
        self.selected_lot_id = None
        self.selected_zone_id = None
        self.selected_slot_id = None
        self.session_filter = "All"
        self.payment_filter = "All"
