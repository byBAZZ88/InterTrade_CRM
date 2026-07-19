"""
InterTrade CRM — экран входа
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LoginDialog(QDialog):
    """Диалог авторизации"""

    def __init__(self, crm, parent=None):
        super().__init__(parent)
        self.crm = crm
        self.setWindowTitle("InterTrade CRM — Login")
        self.setMinimumSize(400, 280)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(14)

        title = QLabel("InterTrade CRM")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Enter your credentials")
        sub.setFont(QFont("Arial", 11))
        sub.setStyleSheet("color: #64748B;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        ins = "padding: 10px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px;"

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet(ins)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setStyleSheet(ins)
        self.password_input.returnPressed.connect(self._login)
        layout.addWidget(self.password_input)

        layout.addStretch()

        login_btn = QPushButton("Login")
        login_btn.setStyleSheet(
            "background-color: #2563EB; color: white; padding: 12px; "
            "font-weight: bold; border-radius: 6px; border: none; font-size: 14px;"
        )
        login_btn.clicked.connect(self._login)
        layout.addWidget(login_btn)

    def _login(self):
        username = self.username_input.text().strip().lower()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Enter username and password.")
            return

        success, msg, role = self.crm.verify_password(username, password)
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Login Failed", msg)
            self.password_input.clear()
            self.password_input.setFocus()