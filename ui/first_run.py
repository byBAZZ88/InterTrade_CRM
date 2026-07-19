"""
InterTrade CRM — первый запуск, настройка системы
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import ALL_CURRENCIES, DEFAULT_CURRENCY


class FirstRunDialog(QDialog):
    """Диалог первой настройки"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("InterTrade CRM — Initial Setup")
        self.setMinimumSize(480, 420)
        self.setModal(True)
        self.organization_name = None
        self.admin_password = None
        self.base_currency = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(14)

        title = QLabel("InterTrade CRM Setup")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("First launch. Configure basic parameters.")
        sub.setFont(QFont("Arial", 11))
        sub.setStyleSheet("color: #64748B;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        ins = "padding: 10px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px;"

        # Название организации
        layout.addWidget(QLabel("Organization name:"))
        self.org_input = QLineEdit()
        self.org_input.setPlaceholderText("e.g. My Company Ltd")
        self.org_input.setStyleSheet(ins)
        self.org_input.setMaxLength(100)
        layout.addWidget(self.org_input)

        # Базовая валюта
        layout.addWidget(QLabel("Base currency:"))
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(ALL_CURRENCIES)
        self.currency_combo.setCurrentText(DEFAULT_CURRENCY)
        self.currency_combo.setStyleSheet(ins)
        layout.addWidget(self.currency_combo)

        # Мастер-пароль (admin)
        layout.addWidget(QLabel("Admin password:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Minimum 6 characters")
        self.pass_input.setStyleSheet(ins)
        layout.addWidget(self.pass_input)

        # Подтверждение
        layout.addWidget(QLabel("Confirm admin password:"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Repeat password")
        self.confirm_input.setStyleSheet(ins)
        self.confirm_input.returnPressed.connect(self._save)
        layout.addWidget(self.confirm_input)

        # Предупреждение
        warn = QFrame()
        warn.setStyleSheet("background-color: #FEF3C7; border: 1px solid #F59E0B; border-radius: 6px;")
        wl = QVBoxLayout(warn)
        wl.setContentsMargins(12, 10, 12, 10)
        wt = QLabel("Warning! Organization name cannot be changed later.\n"
                     "Write down the admin password — it cannot be recovered.")
        wt.setFont(QFont("Arial", 9))
        wt.setStyleSheet("color: #92400E;")
        wt.setWordWrap(True)
        wl.addWidget(wt)
        layout.addWidget(warn)

        layout.addStretch()

        save_btn = QPushButton("Create Database")
        save_btn.setStyleSheet(
            "background-color: #2563EB; color: white; padding: 14px; "
            "font-weight: bold; border-radius: 6px; border: none; font-size: 14px;"
        )
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _save(self):
        org = self.org_input.text().strip()
        pwd = self.pass_input.text()
        confirm = self.confirm_input.text()

        if not org:
            QMessageBox.warning(self, "Error", "Enter organization name.")
            self.org_input.setFocus()
            return

        if len(pwd) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters.")
            self.pass_input.setFocus()
            return

        if pwd != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            self.confirm_input.setFocus()
            return

        self.organization_name = org
        self.admin_password = pwd
        self.base_currency = self.currency_combo.currentText()
        self.accept()