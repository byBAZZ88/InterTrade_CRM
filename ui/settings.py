"""
InterTrade CRM — настройки
"""

import os
import hashlib
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QScrollArea,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QFormLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import pandas as pd
from config import ALL_CURRENCIES, ALL_COUNTRIES, ROLES, ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_USER


class SettingsTab(QWidget):
    """Настройки — справочники, пользователи, пароль, экспорт"""

    def __init__(self, crm):
        super().__init__()
        self.crm = crm
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        sw = QWidget()
        svl = QVBoxLayout(sw)
        svl.setContentsMargins(30, 30, 30, 30)
        svl.setSpacing(18)

        title = QLabel("System Settings")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")
        svl.addWidget(title)

        ins = "padding: 8px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 4px;"
        btn_style = "padding: 10px; border-radius: 4px; border: none; font-weight: bold; font-size: 13px;"

        # ─── Справочники (только admin) ────────────────────────────
        if self.crm.current_role == ROLE_ADMIN:
            rf = QFrame()
            rf.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
            rl = QVBoxLayout(rf)
            rl.setSpacing(10)
            rl.addWidget(QLabel("Reference Books"))

            rl.addWidget(QLabel("Activity Types (comma separated):"))
            self.types_input = QLineEdit(", ".join(self.crm.get_activity_types()))
            self.types_input.setStyleSheet(ins)
            rl.addWidget(self.types_input)

            rl.addWidget(QLabel("Lead Sources (comma separated):"))
            self.sources_input = QLineEdit(", ".join(self.crm.get_lead_sources()))
            self.sources_input.setStyleSheet(ins)
            rl.addWidget(self.sources_input)

            save_rules_btn = QPushButton("Save Reference Books")
            save_rules_btn.setStyleSheet(f"background-color: #2563EB; color: white; {btn_style}")
            save_rules_btn.clicked.connect(self._save_reference_books)
            rl.addWidget(save_rules_btn)
            svl.addWidget(rf)

        # ─── Управление пользователями (только admin) ───────────────
        if self.crm.current_role in (ROLE_ADMIN, ROLE_SUPERVISOR):
            uf = QFrame()
            uf.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
            ul = QVBoxLayout(uf)
            ul.setSpacing(10)

            ul.addWidget(QLabel("User Management"))

            self.users_table = QTableWidget()
            self.users_table.setColumnCount(4)
            self.users_table.setHorizontalHeaderLabels(["Username", "Role", "Active", "Created"])
            self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.users_table.setMinimumHeight(180)
            self.users_table.setMaximumHeight(300)
            self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.users_table.setStyleSheet("""
                QTableWidget { background-color: #FFFFFF; border: 1px solid #E2E8F0; }
                QHeaderView::section { background-color: #F1F5F9; padding: 6px; }
            """)
            self.users_table.itemClicked.connect(self._on_user_selected)
            self._refresh_users_table()
            ul.addWidget(self.users_table)

            # Форма редактирования / добавления
            edit_row1 = QHBoxLayout()
            self.edit_username = QLineEdit()
            self.edit_username.setPlaceholderText("Username")
            self.edit_username.setStyleSheet(ins)
            edit_row1.addWidget(QLabel("User:"))
            edit_row1.addWidget(self.edit_username)

            self.edit_password = QLineEdit()
            self.edit_password.setPlaceholderText("New password (leave empty to keep)")
            self.edit_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.edit_password.setStyleSheet(ins)
            edit_row1.addWidget(QLabel("Pass:"))
            edit_row1.addWidget(self.edit_password)

            self.edit_role = QComboBox()
            if self.crm.current_role == ROLE_ADMIN:
                self.edit_role.addItems(ROLES)
            else:
                self.edit_role.addItems([ROLE_USER])
            self.edit_role.setStyleSheet(ins)
            edit_row1.addWidget(QLabel("Role:"))
            edit_row1.addWidget(self.edit_role)
            ul.addLayout(edit_row1)

            btn_row = QHBoxLayout()

            save_btn = QPushButton("Save / Update")
            save_btn.setStyleSheet(f"background-color: #2563EB; color: white; {btn_style}")
            save_btn.clicked.connect(self._save_user)
            btn_row.addWidget(save_btn)

            toggle_btn = QPushButton("Toggle Active")
            toggle_btn.setStyleSheet(f"background-color: #8B5CF6; color: white; {btn_style}")
            toggle_btn.clicked.connect(self._toggle_user)
            btn_row.addWidget(toggle_btn)

            delete_btn = QPushButton("Delete User")
            delete_btn.setStyleSheet(f"background-color: #EF4444; color: white; {btn_style}")
            delete_btn.clicked.connect(self._delete_user)
            btn_row.addWidget(delete_btn)

            clear_btn = QPushButton("Clear Form")
            clear_btn.setStyleSheet(f"background-color: #E2E8F0; color: #475569; {btn_style}")
            clear_btn.clicked.connect(self._clear_user_form)
            btn_row.addWidget(clear_btn)

            ul.addLayout(btn_row)
            svl.addWidget(uf)

        # ─── Смена пароля ───────────────────────────────────────────
        pf = QFrame()
        pf.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
        pl = QVBoxLayout(pf)
        pl.setSpacing(8)
        pl.addWidget(QLabel("Change Password"))

        self.old_pass = QLineEdit()
        self.old_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_pass.setPlaceholderText("Current password")
        self.old_pass.setStyleSheet(ins)
        pl.addWidget(self.old_pass)

        self.new_pass = QLineEdit()
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass.setPlaceholderText("New password")
        self.new_pass.setStyleSheet(ins)
        pl.addWidget(self.new_pass)

        save_pass_btn = QPushButton("Change Password")
        save_pass_btn.setStyleSheet(f"background-color: #2563EB; color: white; {btn_style}")
        save_pass_btn.clicked.connect(self._change_password)
        pl.addWidget(save_pass_btn)
        svl.addWidget(pf)

        # ─── Экспорт базы (supervisor+) ─────────────────────────────
        if self.crm.current_role in (ROLE_ADMIN, ROLE_SUPERVISOR):
            ef = QFrame()
            ef.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
            el = QVBoxLayout(ef)
            el.setSpacing(10)
            el.addWidget(QLabel("Data Export (Open Format)"))

            export_btn = QPushButton("Export Database to Excel")
            export_btn.setStyleSheet(f"background-color: #10B981; color: white; {btn_style}")
            export_btn.clicked.connect(self._export_database)
            el.addWidget(export_btn)
            svl.addWidget(ef)

        svl.addStretch()
        scroll.setWidget(sw)
        layout.addWidget(scroll)

    # ═══════════════════════════════════════════════════════════════════
    #  ОБРАБОТЧИКИ
    # ═══════════════════════════════════════════════════════════════════

    def _save_reference_books(self):
        types = [t.strip() for t in self.types_input.text().split(",") if t.strip()]
        sources = [s.strip() for s in self.sources_input.text().split(",") if s.strip()]

        if not types or not sources:
            QMessageBox.warning(self, "Warning", "All reference books must have at least one value.")
            return

        config = self.crm._load_config()
        config["activity_types"] = types
        config["lead_sources"] = sources
        self.crm._save_config(config)

    def _refresh_users_table(self):
        users = self.crm.get_users()
        self.users_table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.users_table.setItem(i, 0, QTableWidgetItem(u["username"]))
            self.users_table.setItem(i, 1, QTableWidgetItem(u["role"]))
            self.users_table.setItem(i, 2, QTableWidgetItem("Yes" if u["is_active"] else "No"))
            self.users_table.setItem(i, 3, QTableWidgetItem(u["created_at"]))

    def _on_user_selected(self, item):
        row = item.row()
        username = self.users_table.item(row, 0).text()
        role = self.users_table.item(row, 1).text()
        self.edit_username.setText(username)
        self.edit_role.setCurrentText(role)
        self.edit_password.clear()

    def _clear_user_form(self):
        self.edit_username.clear()
        self.edit_password.clear()
        self.edit_role.setCurrentIndex(0)
        self.users_table.clearSelection()

    def _save_user(self):
        username = self.edit_username.text().strip().lower()
        password = self.edit_password.text()
        role = self.edit_role.currentText()
        # Supervisor не может создавать/менять Admin и Supervisor
        if self.crm.current_role == ROLE_SUPERVISOR and role != ROLE_USER:
            QMessageBox.warning(self, "Error", "Supervisor can only manage Users.")
            return

        if not username:
            QMessageBox.warning(self, "Error", "Username is required.")
            return

        users = self.crm.get_users()
        existing = next((u for u in users if u["username"] == username), None)

        if existing:
            # Обновление существующего
            if password:
                new_hash = hashlib.sha256(password.encode()).hexdigest()
                self.crm.cursor.execute(
                    "UPDATE users SET password_hash = ?, role = ? WHERE username = ?",
                    (new_hash, role, username),
                )
            else:
                self.crm.cursor.execute(
                    "UPDATE users SET role = ? WHERE username = ?",
                    (role, username),
                )
            self.crm.conn.commit()
            QMessageBox.information(self, "Success", f"User '{username}' updated.")
        else:
            # Новый пользователь
            if len(password) < 4:
                QMessageBox.warning(self, "Error", "Password min 4 characters for new user.")
                return
            success, msg = self.crm.add_user(username, password, role)
            if not success:
                QMessageBox.critical(self, "Error", msg)
                return
            QMessageBox.information(self, "Success", msg)

        self._refresh_users_table()
        self._clear_user_form()

    def _toggle_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a user in the table.")
            return
        username = self.users_table.item(row, 0).text()
        users = self.crm.get_users()
        user = next((u for u in users if u["username"] == username), None)
        if self.crm.current_role == ROLE_SUPERVISOR and user and user["role"] != ROLE_USER:
            QMessageBox.warning(self, "Error", "Supervisor cannot modify Admin or Supervisor accounts.")
            return
        if username == "admin":
            QMessageBox.warning(self, "Error", "Cannot deactivate admin.")
            return

        user = next((u for u in users if u["username"] == username), None)
        if user:
            self.crm.toggle_user_active(user["id"])
            self._refresh_users_table()
            QMessageBox.information(self, "Success", f"User '{username}' toggled.")

    def _delete_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a user in the table.")
            return
        username = self.users_table.item(row, 0).text()
        users = self.crm.get_users()
        user = next((u for u in users if u["username"] == username), None)
        if username == "admin":
            QMessageBox.warning(self, "Error", "Cannot delete admin.")
            return
        if self.crm.current_role == ROLE_SUPERVISOR and user and user["role"] != ROLE_USER:
            QMessageBox.warning(self, "Error", "Supervisor can only delete Users.")
            return
        if self.crm.current_role != ROLE_ADMIN:
            QMessageBox.warning(self, "Error", "Only admin can delete users.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete user '{username}'? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.crm.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.crm.conn.commit()
        self._refresh_users_table()
        self._clear_user_form()
        QMessageBox.information(self, "Success", f"User '{username}' deleted.")

    def _change_password(self):
        old = self.old_pass.text()
        new = self.new_pass.text().strip()

        if len(new) < 6:
            QMessageBox.warning(self, "Warning", "New password min 6 characters.")
            return

        success, msg, _ = self.crm.verify_password(self.crm.current_user, old)
        if not success:
            QMessageBox.critical(self, "Error", "Current password is incorrect.")
            return

        new_hash = hashlib.sha256(new.encode()).hexdigest()
        self.crm.cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_hash, self.crm.current_user),
        )
        self.crm.conn.commit()
        self.old_pass.clear()
        self.new_pass.clear()
        QMessageBox.information(self, "Success", "Password changed.")

    def _export_database(self):
        try:
            clients = self.crm.get_all_counterparties()
            export_data = []
            for c in clients:
                export_data.append({
                    "Name": c["name"],
                    "Trade Name": c.get("trade_name", ""),
                    "Tax ID": c["tax_id"],
                    "VAT ID": c.get("vat_id", ""),
                    "Country": c["country"],
                    "Phone": c["phone"],
                    "Email": c["email"],
                    "Contact Person": c["contact_person"],
                    "Activity Type": c["activity_type"],
                    "Lead Source": c["lead_source"],
                    "Currency": c["currency"],
                    "Assigned To": c["assigned_to"],
                    "Status": c["status"],
                    "Sales Amount": c["sales_amount"] or 0,
                    "Last Sale Date": c["last_sale_date"],
                    "Created": c["created_at"],
                    "Next Contact": c.get("next_contact_date", ""),
                    "Last Comment": c["last_comment"],
                    "Description": c.get("description", ""),
                    "Created By": c.get("created_by", ""),
                })

            df = pd.DataFrame(export_data)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = f"InterTrade_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(desktop, filename)
            df.to_excel(filepath, index=False)

            QMessageBox.information(self, "Success", f"File saved to Desktop:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def is_locked(self):
        return self.crm.is_settings_locked()