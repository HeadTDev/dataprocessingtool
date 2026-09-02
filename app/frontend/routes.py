from dataclasses import dataclass
from typing import Callable

from app.frontend.modules.barcode_pdf.view import BarcodeCopierWindow
from app.frontend.modules.cofanet.view import CofanetHelpUI
from app.frontend.modules.ksh.view import MainUI as KshView
from app.frontend.modules.merkantil.view import MainUI as MerkantilView
from app.frontend.modules.mouse_mover.view import MainUI as MouseMoverView


@dataclass(frozen=True, slots=True)
class AppRoute:
    id: str
    label: str
    icon: str
    qta_icon: str
    # A QWidget for the 4 nav-driven pages; the pinned mouse_mover route uses
    # a plain coordinator object instead (see mouse_mover/view.py:MainUI).
    view_class: Callable[[], object]
    enabled: bool = True
    pinned: bool = False


ROUTES = [
    AppRoute("merkantil", "Merkantil PDF Feldolgozó", "otp_icon.png", "car", MerkantilView),
    AppRoute("barcode_pdf", "Vonalkód PDF Másolás", "pdf_icon.png", "barcode", BarcodeCopierWindow),
    AppRoute("cofanet", "Cofanet Help", "coface_icon.png", "receipt", CofanetHelpUI),
    AppRoute("ksh", "KSH Iparági Értékesítés", "ksh_icon.png", "chart-line-up", KshView),
    AppRoute("mouse_mover", "Mouse Mover", "mouse_icon.png", "cursor", MouseMoverView, pinned=True),
]
