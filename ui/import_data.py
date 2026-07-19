"""
InterTrade CRM — универсальный импорт данных из CSV/Excel
"""

import os
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QFileDialog, QProgressBar, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import pandas as pd
from cryptography.fernet import Fernet
import json


class ImportThread(QThread):
    """Фоновый поток импорта"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path, crm):
        super().__init__()
        self.file_path = file_path
        self.crm = crm
        self.db_name = crm.db_name
        self.crypto_key = crm.crypto_key
        self.fernet = Fernet(self.crypto_key)
        self.current_user = crm.current_user

    def _encrypt_val(self, val):
        if val is None or val == "":
            return ""
        return self.fernet.encrypt(str(val).encode()).decode()

    def _decrypt_val(self, val):
        if val is None or val == "":
            return ""
        try:
            return self.fernet.decrypt(val.encode()).decode()
        except Exception:
            return ""

    def run(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Определяем формат файла
            ext = os.path.splitext(self.file_path)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(self.file_path)
            else:
                df = pd.read_excel(self.file_path)

            total = len(df)
            updated = 0
            created = 0
            skipped = 0

            today = datetime.now().strftime("%Y-%m-%d")

            for idx, row in df.iterrows():
                row_num = idx + 2

                try:
                    name = str(row.get("Name", row.get("name", ""))).strip()
                    tax_id = str(row.get("Tax ID", row.get("tax_id", row.get("taxid", "")))).strip()
                    country = str(row.get("Country", row.get("country", ""))).strip().upper()[:2]
                    phone = str(row.get("Phone", row.get("phone", ""))).strip()
                    email = str(row.get("Email", row.get("email", ""))).strip()
                    contact_person = str(row.get("Contact Person", row.get("contact_person", row.get("contact", "")))).strip()
                    activity_type = str(row.get("Activity Type", row.get("activity_type", ""))).strip()
                    lead_source = str(row.get("Lead Source", row.get("lead_source", ""))).strip()
                    currency = str(row.get("Currency", row.get("currency", ""))).strip().upper()
                    assigned_to = str(row.get("Assigned To", row.get("assigned_to", ""))).strip()
                    sales_amount_str = str(row.get("Sales Amount", row.get("sales_amount", "0"))).strip()
                    last_sale_date = str(row.get("Last Sale Date", row.get("last_sale_date", ""))).strip()
                    status = str(row.get("Status", row.get("status", ""))).strip()
                    trade_name = str(row.get("Trade Name", row.get("trade_name", ""))).strip()
                    vat_id = str(row.get("VAT ID", row.get("vat_id", ""))).strip()
                    description = str(row.get("Description", row.get("description", ""))).strip()

                    # Очистка от NaN
                    for var in [name, tax_id, country, phone, email, contact_person,
                                activity_type, lead_source, currency, assigned_to,
                                last_sale_date, status, trade_name, vat_id, description]:
                        if var in ["nan", "NaN", "None", ""]:
                            var = ""

                    if not name or not tax_id:
                        skipped += 1
                        continue

                    if not country:
                        country = "US"

                    try:
                        sales_amount = float(sales_amount_str) if sales_amount_str not in ["nan", "NaN", ""] else 0.0
                    except ValueError:
                        sales_amount = 0.0

                    if currency not in ["USD", "EUR", "RUB", "GBP", "CNY", "JPY", "CHF"]:
                        currency = "USD"

                    # Матчинг по tax_id + country
                    cursor.execute(
                        "SELECT id, sales_amount FROM counterparties WHERE tax_id = ? AND country = ?",
                        (self._encrypt_val(tax_id), country),
                    )
                    existing = cursor.fetchone()

                    if existing:
                        # Обновление
                        cp_id = existing[0]
                        new_sales = (existing[1] or 0.0) + sales_amount
                        cursor.execute(
                            "UPDATE counterparties SET sales_amount = ?, last_sale_date = ?, phone = ?, email = ?, contact_person = ? WHERE id = ?",
                            (new_sales, self._encrypt_val(last_sale_date) if last_sale_date else None,
                             self._encrypt_val(phone) if phone else None,
                             self._encrypt_val(email) if email else None,
                             self._encrypt_val(contact_person) if contact_person else None,
                             cp_id),
                        )
                        conn.commit()
                        updated += 1
                    else:
                        # Создание нового
                        cursor.execute("""
                            INSERT INTO counterparties (
                                name, trade_name, tax_id, vat_id, country,
                                phone, email, contact_person,
                                activity_type, lead_source, currency, assigned_to,
                                status, sales_amount, last_sale_date,
                                created_at, next_contact_date, last_comment, description, created_by
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            self._encrypt_val(name),
                            self._encrypt_val(trade_name) if trade_name else None,
                            self._encrypt_val(tax_id),
                            self._encrypt_val(vat_id) if vat_id else None,
                            country,
                            self._encrypt_val(phone) if phone else None,
                            self._encrypt_val(email) if email else None,
                            self._encrypt_val(contact_person) if contact_person else None,
                            self._encrypt_val(activity_type) if activity_type else None,
                            self._encrypt_val(lead_source) if lead_source else None,
                            currency if currency else "USD",
                            self._encrypt_val(assigned_to) if assigned_to else None,
                            status if status else "New",
                            sales_amount,
                            self._encrypt_val(last_sale_date) if last_sale_date else None,
                            self._encrypt_val(today),
                            None,
                            None,
                            self._encrypt_val(description) if description else None,
                            self.current_user,
                        ))
                        cp_id = cursor.lastrowid
                        cursor.execute(
                            "INSERT INTO status_history (counterparty_id, status_name, changed_at, changed_by) VALUES (?, ?, ?, ?)",
                            (cp_id, status if status else "New", today, self.current_user),
                        )
                        conn.commit()
                        created += 1

                except Exception:
                    skipped += 1

                self.progress.emit(int((idx + 1) / total * 100))

            conn.close()
            self.finished.emit({
                "total": total,
                "updated": updated,
                "created": created,
                "skipped": skipped,
            })

        except Exception as e:
            self.error.emit(str(e))


class ImportDataTab(QWidget):
    """Вкладка «Import Data» — универсальный импорт из CSV/Excel"""

    def __init__(self, crm):
        super().__init__()
        self.crm = crm
        self.file_path = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Информация
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px;")
        il = QVBoxLayout(info_frame)
        il.setContentsMargins(24, 20, 24, 20)
        il.setSpacing(12)

        title = QLabel("Import Data")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")
        il.addWidget(title)

        hint = QLabel(
            "Required column order in file (first row = headers):\n\n"
            "Name | Trade Name | Tax ID | VAT ID | Country | Phone | Email |\n"
            "Contact Person | Activity Type | Lead Source | Currency |\n"
            "Assigned To | Sales Amount | Last Sale Date | Status | Description\n\n"
            "• Matching is done by Tax ID + Country.\n"
            "• If a match is found — sales amount is added, contacts updated.\n"
            "• If no match — new counterparty is created.\n"
            "• Supported formats: .xlsx, .xls, .csv"
        )
        hint.setFont(QFont("Arial", 10))
        hint.setStyleSheet("color: #475569; line-height: 150%;")
        hint.setWordWrap(True)
        il.addWidget(hint)

        layout.addWidget(info_frame)

        # Выбор файла
        file_row = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #94A3B8; font-style: italic; padding: 8px;")
        file_row.addWidget(self.file_label, stretch=1)

        browse_btn = QPushButton("Select File (.xlsx, .xls, .csv)")
        browse_btn.setStyleSheet(
            "background-color: #2563EB; color: white; padding: 12px 24px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"
        )
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Кнопка запуска
        self.start_btn = QPushButton("Start Import")
        self.start_btn.setStyleSheet(
            "background-color: #10B981; color: white; padding: 14px 32px; font-weight: bold; border-radius: 8px; border: none; font-size: 14px;"
        )
        self.start_btn.clicked.connect(self._start_import)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select file", "",
            "Excel/CSV files (*.xlsx *.xls *.csv);;All files (*.*)"
        )
        if path:
            self.file_path = path
            self.file_label.setText(os.path.basename(path))
            self.file_label.setStyleSheet("color: #059669; font-weight: bold; padding: 8px;")
            self.start_btn.setEnabled(True)

    def _start_import(self):
        if not self.file_path:
            return

        reply = QMessageBox.question(
            self, "Confirm",
            "Start import?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.start_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Importing...")

        self.thread = ImportThread(self.file_path, self.crm)
        self.thread.progress.connect(self._on_progress)
        self.thread.finished.connect(self._on_finished)
        self.thread.error.connect(self._on_error)
        self.thread.start()

    def _on_progress(self, value):
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Importing... {value}%")

    def _on_finished(self, result):
        self.progress_bar.setValue(100)
        self.status_label.setText("Import completed")

        msg = (
            f"Import Results:\n\n"
            f"Total rows: {result['total']}\n"
            f"Updated: {result['updated']}\n"
            f"Created: {result['created']}\n"
            f"Skipped: {result['skipped']}"
        )
        QMessageBox.information(self, "Import Completed", msg)
        self.start_btn.setEnabled(True)
        self.crm.refresh_connection()

    def _on_error(self, error_msg):
        self.status_label.setText("Import error")
        QMessageBox.critical(self, "Error", f"Import failed:\n{error_msg}")
        self.start_btn.setEnabled(True)
        self.progress_bar.setVisible(False)