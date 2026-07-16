from dataclasses import dataclass
from typing import Type

from PySide6.QtWidgets import QWidget

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
    view_class: Type[QWidget]
    enabled: bool = True


ROUTES = [
    AppRoute("merkantil", "💸 Merkantil PDF Feldolgozó", "otp_icon.png", MerkantilView),
    AppRoute("barcode_pdf", "📂 Vonalkód PDF Másolás", "pdf_icon.png", BarcodeCopierWindow),
    AppRoute("cofanet", "📚 Cofanet Help", "coface_icon.png", CofanetHelpUI),
    AppRoute("ksh", "🔧 KSH Iparági Értékesítés", "ksh_icon.png", KshView),
    AppRoute("mouse_mover", "🖱️ Mouse Mover", "mouse_icon.png", MouseMoverView),
]
