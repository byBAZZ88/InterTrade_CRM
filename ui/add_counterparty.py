"""
InterTrade CRM — диалог добавления контрагента
"""

import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QGroupBox,
    QComboBox, QTextEdit, QScrollArea, QWidget, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import ALL_COUNTRIES, DEFAULT_COUNTRY, ALL_CURRENCIES


class AddCounterpartyDialog(QDialog):
    """Диалог добавления нового контрагента"""

    def __init__(self, crm, parent=None):
        super().__init__(parent)
        self.crm = crm
        self.setWindowTitle("Add Counterparty")
        self.setMinimumSize(500, 425)
        self.resize(550, 640)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        sw = QWidget()
        sw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        layout = QVBoxLayout(sw)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("New Counterparty")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")
        layout.addWidget(title)

        ins = "padding: 6px 8px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 4px; font-size: 13px;"
        min_h = "min-height: 24px;"

        # ─── Идентификация ──────────────────────────────────────────
        g1 = QGroupBox("Identification")
        g1.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        f1 = QFormLayout(g1)
        f1.setSpacing(6)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Official company name *")
        self.name_input.setStyleSheet(ins + min_h)
        self.name_input.setMaxLength(200)
        self.name_input.setMinimumHeight(24)
        f1.addRow("Company Name *:", self.name_input)

        self.trade_name_input = QLineEdit()
        self.trade_name_input.setPlaceholderText("Trading name / DBA")
        self.trade_name_input.setStyleSheet(ins + min_h)
        self.trade_name_input.setMaxLength(200)
        self.trade_name_input.setMinimumHeight(24)
        f1.addRow("Trade Name:", self.trade_name_input)

        self.tax_id_input = QLineEdit()
        self.tax_id_input.setPlaceholderText("National registration number *")
        self.tax_id_input.setStyleSheet(ins + min_h)
        self.tax_id_input.setMaxLength(50)
        self.tax_id_input.setMinimumHeight(24)
        f1.addRow("Tax ID *:", self.tax_id_input)

        self.vat_id_input = QLineEdit()
        self.vat_id_input.setPlaceholderText("VAT ID (optional)")
        self.vat_id_input.setStyleSheet(ins + min_h)
        self.vat_id_input.setMaxLength(50)
        self.vat_id_input.setMinimumHeight(24)
        f1.addRow("VAT ID:", self.vat_id_input)

        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        for code, name in ALL_COUNTRIES.items():
            self.country_combo.addItem(f"{code} - {name}", code)
        self.country_combo.setCurrentText(f"{DEFAULT_COUNTRY} - {ALL_COUNTRIES.get(DEFAULT_COUNTRY, '')}")
        self.country_combo.setStyleSheet(ins + min_h)
        self.country_combo.setMinimumHeight(24)
        f1.addRow("Country *:", self.country_combo)

        layout.addWidget(g1)

        # ─── Контакты ───────────────────────────────────────────────
        g2 = QGroupBox("Contacts")
        g2.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        f2 = QFormLayout(g2)
        f2.setSpacing(6)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Numbers only, comma separated")
        self.phone_input.setStyleSheet(ins + min_h)
        self.phone_input.setMaxLength(100)
        self.phone_input.setMinimumHeight(24)
        f2.addRow("Phone:", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        self.email_input.setStyleSheet(ins + min_h)
        self.email_input.setMinimumHeight(24)
        f2.addRow("Email:", self.email_input)

        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("Contact person name")
        self.contact_person_input.setStyleSheet(ins + min_h)
        self.contact_person_input.setMinimumHeight(24)
        f2.addRow("Contact Person:", self.contact_person_input)

        layout.addWidget(g2)

        # ─── Классификация ──────────────────────────────────────────
        g3 = QGroupBox("Classification")
        g3.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        f3 = QFormLayout(g3)
        f3.setSpacing(6)

        self.lead_combo = QComboBox()
        self.lead_combo.setEditable(True)
        self.lead_combo.addItems(self.crm.get_lead_sources())
        self.lead_combo.setCurrentText("Website")
        self.lead_combo.setStyleSheet(ins + min_h)
        self.lead_combo.setMinimumHeight(24)
        f3.addRow("Lead Source:", self.lead_combo)

        self.activity_combo = QComboBox()
        self.activity_combo.setEditable(True)
        self.activity_combo.addItems(self.crm.get_activity_types())
        self.activity_combo.setCurrentText("Professional Services")
        self.activity_combo.setStyleSheet(ins + min_h)
        self.activity_combo.setMinimumHeight(24)
        f3.addRow("Activity Type:", self.activity_combo)

        self.currency_combo = QComboBox()
        self.currency_combo.addItems(ALL_CURRENCIES)
        self.currency_combo.setCurrentText(self.crm.get_base_currency())
        self.currency_combo.setStyleSheet(ins + min_h)
        self.currency_combo.setMinimumHeight(24)
        f3.addRow("Currency:", self.currency_combo)

        self.assigned_to_input = QLineEdit()
        self.assigned_to_input.setPlaceholderText("Assigned manager")
        self.assigned_to_input.setStyleSheet(ins + min_h)
        self.assigned_to_input.setText(self.crm.current_user if self.crm.current_user else "")
        self.assigned_to_input.setMinimumHeight(24)
        f3.addRow("Assigned To:", self.assigned_to_input)

        layout.addWidget(g3)

        # ─── Дополнительно ──────────────────────────────────────────
        g4 = QGroupBox("Additional")
        g4.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        f4 = QFormLayout(g4)
        f4.setSpacing(6)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description (up to 200 characters)")
        self.desc_input.setMinimumHeight(50)
        self.desc_input.setMaximumHeight(75)
        self.desc_input.setStyleSheet(ins)
        f4.addRow("Description:", self.desc_input)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("First contact details, agreements...")
        self.comment_input.setMinimumHeight(60)
        self.comment_input.setMaximumHeight(85)
        self.comment_input.setStyleSheet(ins)
        f4.addRow("Comment:", self.comment_input)

        layout.addWidget(g4)

        # ─── Кнопки ─────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        save_btn = QPushButton("Save Counterparty")
        save_btn.setMinimumHeight(34)
        save_btn.setStyleSheet(
            "background-color: #2563EB; color: white; padding: 10px 24px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"
        )
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(34)
        cancel_btn.setStyleSheet(
            "background-color: #E2E8F0; color: #475569; padding: 10px 24px; border-radius: 6px; border: none; font-size: 13px;"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        scroll.setWidget(sw)
        outer.addWidget(scroll)

    def _save(self):
        name = self.name_input.text().strip()
        trade_name = self.trade_name_input.text().strip()
        tax_id = self.tax_id_input.text().strip()
        vat_id = self.vat_id_input.text().strip()
        country = self.country_combo.currentData()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        contact_person = self.contact_person_input.text().strip()
        lead_source = self.lead_combo.currentText().strip()
        activity_type = self.activity_combo.currentText().strip()
        currency = self.currency_combo.currentText()
        assigned_to = self.assigned_to_input.text().strip()
        description = self.desc_input.toPlainText().strip()[:200]
        comment = self.comment_input.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Company name is required.")
            self.name_input.setFocus()
            return

        if not tax_id:
            QMessageBox.warning(self, "Error", "Tax ID is required.")
            self.tax_id_input.setFocus()
            return

        if not country:
            QMessageBox.warning(self, "Error", "Country is required.")
            self.country_combo.setFocus()
            return

        phone_clean = re.sub(r"[^0-9,]", "", phone)
        phone_clean = ", ".join(p.strip() for p in phone_clean.split(",") if p.strip())

        success, result = self.crm.add_counterparty(
            name=name,
            trade_name=trade_name,
            tax_id=tax_id,
            vat_id=vat_id,
            country=country,
            phone=phone_clean,
            email=email,
            contact_person=contact_person,
            activity_type=activity_type,
            lead_source=lead_source if lead_source else "Website",
            currency=currency,
            assigned_to=assigned_to,
            comment=comment,
            description=description,
        )

        if not success:
            QMessageBox.critical(self, "Error", result)
            return

        QMessageBox.information(self, "Success", f"Counterparty '{name}' added.")
        self.accept()