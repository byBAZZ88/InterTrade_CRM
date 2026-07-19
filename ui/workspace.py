"""
InterTrade CRM — рабочий стол: поиск, карточка, фиксация контактов
"""

import re
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QLineEdit,
    QPushButton, QMessageBox, QScrollArea, QComboBox,
    QSplitter, QTextEdit, QFormLayout, QGroupBox, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from config import (
    STATUS_NEW, STATUS_VERIFICATION, STATUS_NEGOTIATION, STATUS_PROPOSAL,
    STATUS_AWAITING_PAYMENT, STATUS_PAID, STATUS_DEAL_CLOSED,
    STATUS_REGULAR, STATUS_RARE, STATUS_SLEEPING,
    STATUS_ON_HOLD, STATUS_CONTACT_BY_DATE, STATUS_BLOCKED,
)


class WorkspaceTab(QWidget):
    """Рабочий стол — поиск, карточка, фиксация контактов"""

    STATUS_COLORS = {
        "New": QColor("#EF4444"),
        "Verification": QColor("#D97706"),
        "Negotiation": QColor("#D97706"),
        "Proposal": QColor("#2563EB"),
        "Awaiting Payment": QColor("#DC2626"),
        "Paid": QColor("#2563EB"),
        "Deal Closed": QColor("#059669"),
        "Regular": QColor("#059669"),
        "Rare": QColor("#92400E"),
        "Sleeping": QColor("#6B7280"),
        "On Hold": QColor("#4338CA"),
        "Contact by Date": QColor("#DC2626"),
        "Blocked": QColor("#94A3B8"),
    }

    LONG_TERM_STATUSES = [
        STATUS_REGULAR, STATUS_RARE, STATUS_SLEEPING,
        STATUS_ON_HOLD, STATUS_CONTACT_BY_DATE, STATUS_BLOCKED,
    ]

    def __init__(self, crm):
        super().__init__()
        self.crm = crm
        self.selected_client = None
        self.edit_mode = False
        self.search_results = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Панель поиска
        sf = QFrame()
        sf.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
        sl = QHBoxLayout(sf)
        sl.setContentsMargins(12, 10, 12, 10)
        sl.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by any field...")
        self.search_input.setStyleSheet(
            "padding: 10px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px;"
        )
        self.search_input.returnPressed.connect(self._perform_search)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", None)
        for s in self.crm.get_statuses():
            self.status_filter.addItem(s, s)
        self.status_filter.setStyleSheet(
            "padding: 8px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px; min-width: 160px;"
        )

        sb = QPushButton("Search")
        sb.setStyleSheet(
            "background-color: #2563EB; color: white; padding: 10px 24px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"
        )
        sb.clicked.connect(self._perform_search)

        ab = QPushButton("+ New Counterparty")
        ab.setStyleSheet(
            "background-color: #10B981; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"
        )
        ab.clicked.connect(self._add_counterparty_dialog)

        sl.addWidget(self.search_input, stretch=3)
        sl.addWidget(self.status_filter)
        sl.addWidget(sb)
        sl.addWidget(ab)
        layout.addWidget(sf)

        # Сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая панель — результаты
        lp = QFrame()
        lp.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px;")
        ll = QVBoxLayout(lp)
        ll.setContentsMargins(8, 8, 8, 8)
        lt = QLabel("Search Results")
        lt.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lt.setStyleSheet("color: #475569; padding: 4px;")
        ll.addWidget(lt)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Name", "Tax ID", "Country", "Status"])
        hdr = self.results_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; border: 1px solid #E2E8F0; gridline-color: #CBD5E1; }
            QHeaderView::section { background-color: #F1F5F9; color: #475569; font-weight: bold; padding: 6px; border: 1px solid #CBD5E1; }
            QTableWidget::item:selected { background-color: #DBEAFE; color: #1E293B; }
        """)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.clicked.connect(self._on_result_selected)
        ll.addWidget(self.results_table)
        splitter.addWidget(lp)

        # Правая панель — карточка
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px;")
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(12, 12, 12, 12)
        self.right_layout.setSpacing(8)
        self._show_placeholder()
        splitter.addWidget(self.right_panel)
        splitter.setSizes([450, 650])

        layout.addWidget(splitter, stretch=1)

    # ═══════════════════════════════════════════════════════════════════
    #  ПОИСК
    # ═══════════════════════════════════════════════════════════════════

    def _show_placeholder(self):
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        p = QLabel("Select a counterparty from the list\nto view details")
        p.setFont(QFont("Arial", 12))
        p.setStyleSheet("color: #94A3B8;")
        p.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p.setWordWrap(True)
        self.right_layout.addWidget(p)
        self.right_layout.addStretch()

    def _perform_search(self):
        query = self.search_input.text().strip().lower()
        status_filter = self.status_filter.currentData()

        if len(query) < 2:
            QMessageBox.warning(self, "Search", "Enter at least 2 characters.")
            return

        all_clients = self.crm.get_all_counterparties()
        results = []
        for c in all_clients:
            if status_filter and c["status"] != status_filter:
                continue
            searchable = " ".join([
                str(c.get(k, "")) for k in [
                    "name", "trade_name", "tax_id", "vat_id", "phone", "email",
                    "contact_person", "lead_source", "activity_type",
                    "last_comment", "description",
                ]
            ]).lower()
            if query not in searchable:
                continue
            results.append(c)

        self.search_results = results
        self._populate_results_table(results)
        self.selected_client = None
        self._show_placeholder()

    def _populate_results_table(self, results):
        self.results_table.setRowCount(len(results))
        for row_idx, client in enumerate(results):
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(client["name"]))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(client["tax_id"]))
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(client["country"]))
            si = QTableWidgetItem(client["status"])
            si.setForeground(self.STATUS_COLORS.get(client["status"], QColor("#000000")))
            self.results_table.setItem(row_idx, 3, si)

    def _on_result_selected(self):
        row = self.results_table.currentRow()
        if row < 0 or row >= len(self.search_results):
            return
        self.selected_client = self.search_results[row]
        self.edit_mode = False
        self._build_client_card_view()
    # ═══════════════════════════════════════════════════════════════════
    #  КАРТОЧКА: ПРОСМОТР
    # ═══════════════════════════════════════════════════════════════════

    def _build_client_card_view(self):
        c = self.selected_client
        if not c:
            return
        self._clear_right_panel()

        ct = QLabel(f"{c['name']}")
        ct.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        ct.setStyleSheet("color: #1E293B; padding: 4px 0;")
        self.right_layout.addWidget(ct)

        slayout = QHBoxLayout()
        st = QLabel(f"Status: {c['status']}")
        st.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        st.setStyleSheet(f"color: {self.STATUS_COLORS.get(c['status'], QColor('#000000')).name()};")
        slayout.addWidget(st)
        slayout.addStretch()
        self.right_layout.addLayout(slayout)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #E2E8F0;")
        sep.setFixedHeight(1)
        self.right_layout.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        sw = QWidget()
        fl = QFormLayout(sw)
        fl.setSpacing(8)
        fl.setContentsMargins(4, 8, 4, 8)

        ls = "font-weight: bold; color: #475569; font-size: 11px;"
        vs = "color: #1E293B; font-size: 12px; padding: 2px 0;"

        def af(label, value):
            lbl = QLabel(label)
            lbl.setStyleSheet(ls)
            val = QLabel(str(value) if value else "-")
            val.setStyleSheet(vs)
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            fl.addRow(lbl, val)

        af("Trade Name", c.get("trade_name", ""))
        af("Tax ID", c["tax_id"])
        af("VAT ID", c.get("vat_id", ""))
        af("Country", c["country"])
        af("Contact Person", c["contact_person"])
        af("Phone", c["phone"])
        af("Email", c["email"])
        af("Activity Type", c["activity_type"])
        af("Lead Source", c["lead_source"])
        af("Currency", c["currency"])
        af("Assigned To", c["assigned_to"])
        af("Sales Amount", f"{(c['sales_amount'] or 0):,.2f} {c['currency']}")
        af("Last Sale Date", c["last_sale_date"])
        af("Created", c["created_at"])
        af("Next Contact", c.get("next_contact_date", ""))
        af("Description", c.get("description", ""))
        af("Last Comment", c["last_comment"])
        af("Created By", c.get("created_by", ""))

        scroll.setWidget(sw)
        self.right_layout.addWidget(scroll, stretch=1)

        ob = QPushButton("Open for Editing")
        ob.setStyleSheet(
            "background-color: #2563EB; color: white; padding: 12px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"
        )
        ob.clicked.connect(self._enter_edit_mode)
        self.right_layout.addWidget(ob)

    # ═══════════════════════════════════════════════════════════════════
    #  КАРТОЧКА: РЕДАКТИРОВАНИЕ
    # ═══════════════════════════════════════════════════════════════════

    def _enter_edit_mode(self):
        self.edit_mode = True
        self._build_client_card_edit()

    def _build_client_card_edit(self):
        c = self.selected_client
        if not c:
            return
        self._clear_right_panel()

        ct = QLabel(f"Editing: {c['name']}")
        ct.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        ct.setStyleSheet("color: #1E293B; padding: 4px 0;")
        self.right_layout.addWidget(ct)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #E2E8F0;")
        sep.setFixedHeight(1)
        self.right_layout.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        sw = QWidget()
        el = QVBoxLayout(sw)
        el.setSpacing(10)

        ins = "padding: 6px 8px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 4px; font-size: 12px;"

        # Реквизиты
        eg = QGroupBox("Counterparty Details")
        eg.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        form = QFormLayout(eg)
        form.setSpacing(8)

        self.edit_phone = QLineEdit(c["phone"])
        self.edit_phone.setPlaceholderText("Numbers only, comma separated")
        self.edit_phone.setStyleSheet(ins)
        form.addRow("Phone:", self.edit_phone)

        self.edit_email = QLineEdit(c["email"])
        self.edit_email.setPlaceholderText("email@example.com")
        self.edit_email.setStyleSheet(ins)
        form.addRow("Email:", self.edit_email)

        self.edit_contact_person = QLineEdit(c["contact_person"])
        self.edit_contact_person.setPlaceholderText("Contact person name")
        self.edit_contact_person.setStyleSheet(ins)
        form.addRow("Contact Person:", self.edit_contact_person)

        self.edit_activity = QComboBox()
        self.edit_activity.setEditable(True)
        self.edit_activity.addItems(self.crm.get_activity_types())
        if c["activity_type"]:
            self.edit_activity.setCurrentText(c["activity_type"])
        self.edit_activity.setStyleSheet(ins)
        form.addRow("Activity Type:", self.edit_activity)

        self.edit_description = QTextEdit()
        self.edit_description.setPlaceholderText("Description (up to 200 characters)")
        self.edit_description.setMaximumHeight(70)
        self.edit_description.setMinimumHeight(50)
        self.edit_description.setStyleSheet(ins)
        if c.get("description"):
            self.edit_description.setPlainText(c["description"])
        form.addRow("Description:", self.edit_description)

        el.addWidget(eg)

        # Фиксация контакта
        cg = QGroupBox("Fix Contact")
        cg.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        cf = QFormLayout(cg)
        cf.setSpacing(8)

        self.contact_status = QComboBox()
        self.contact_status.addItems(self.crm.get_statuses())
        self.contact_status.setCurrentText(c["status"])
        self.contact_status.setStyleSheet(ins)
        cf.addRow("New Status:", self.contact_status)

        self.next_contact_date = QDateEdit()
        self.next_contact_date.setCalendarPopup(True)
        self.next_contact_date.setDisplayFormat("yyyy-MM-dd")
        self.next_contact_date.setMinimumDate(QDate.currentDate())
        self.next_contact_date.setMinimumWidth(140)
        if c.get("next_contact_date"):
            try:
                dt = datetime.strptime(c["next_contact_date"].split(" ")[0], "%Y-%m-%d")
                self.next_contact_date.setDate(QDate(dt.year, dt.month, dt.day))
            except Exception:
                pass
        cf.addRow("Next Contact:", self.next_contact_date)

        self.contact_comment = QTextEdit()
        self.contact_comment.setPlaceholderText("Describe the result of contact...")
        self.contact_comment.setMaximumHeight(100)
        self.contact_comment.setStyleSheet(ins)
        cf.addRow("Comment:", self.contact_comment)

        fb = QPushButton("Fix Contact")
        fb.setStyleSheet(
            "background-color: #10B981; color: white; padding: 10px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"
        )
        fb.clicked.connect(self._fix_contact)
        cf.addRow(fb)
        el.addWidget(cg)

        bb = QPushButton("Back to View")
        bb.setStyleSheet(
            "background-color: #E2E8F0; color: #475569; padding: 8px; border-radius: 4px; border: none; font-weight: bold;"
        )
        bb.clicked.connect(self._exit_edit_mode)
        el.addWidget(bb)
        el.addStretch()

        scroll.setWidget(sw)
        self.right_layout.addWidget(scroll, stretch=1)

    def _exit_edit_mode(self):
        self.edit_mode = False
        self._build_client_card_view()

    def _clear_right_panel(self):
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ═══════════════════════════════════════════════════════════════════
    #  ФИКСАЦИЯ КОНТАКТА
    # ═══════════════════════════════════════════════════════════════════

    def _fix_contact(self):
        if not self.selected_client:
            return
        c = self.selected_client
        new_status = self.contact_status.currentText()
        comment = self.contact_comment.toPlainText().strip()

        if not comment:
            QMessageBox.warning(self, "Attention", "Comment is required.")
            return

        # Нельзя повторно присвоить New
        if new_status == STATUS_NEW and c["status"] != STATUS_NEW:
            QMessageBox.critical(self, "Error", "Cannot reassign 'New' status.")
            return

        phone_raw = self.edit_phone.text().strip()
        phone_clean = re.sub(r"[^0-9,]", "", phone_raw)
        phone_clean = ", ".join(p.strip() for p in phone_clean.split(",") if p.strip())

        email = self.edit_email.text().strip()
        contact_person = self.edit_contact_person.text().strip()
        activity_type = self.edit_activity.currentText().strip()
        description = self.edit_description.toPlainText().strip()
        next_contact = self.next_contact_date.date().toString("yyyy-MM-dd")

        # Проверка даты для Contact by Date и Deal Closed
        if new_status in [STATUS_CONTACT_BY_DATE, STATUS_DEAL_CLOSED]:
            try:
                next_dt = datetime.strptime(next_contact, "%Y-%m-%d")
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if next_dt <= today:
                    QMessageBox.critical(self, "Error",
                        "Next contact date must be in the future.")
                    return
            except ValueError:
                QMessageBox.critical(self, "Error", "Invalid date format.")
                return

        # Проверка обязательных полей для Negotiation
        if new_status == STATUS_NEGOTIATION:
            errors = []
            if not phone_clean:
                errors.append("- Phone")
            if not email:
                errors.append("- Email")
            if not contact_person:
                errors.append("- Contact Person")
            if not activity_type:
                errors.append("- Activity Type")
            if errors:
                QMessageBox.critical(self, "Required Fields",
                    "To move to Negotiation, fill in:\n" + "\n".join(errors))
                return

        # Обновление реквизитов
        self.crm.update_counterparty_fields(
            c["id"],
            phone=phone_clean,
            email=email,
            contact_person=contact_person,
            activity_type=activity_type,
            description=description,
        )

        # Обновление статуса
        self.crm.update_counterparty_status(
            c["id"], new_status, comment,
            next_contact_date=next_contact if next_contact else None,
        )

        # Обновляем локальный объект
        c["phone"] = phone_clean
        c["email"] = email
        c["contact_person"] = contact_person
        c["activity_type"] = activity_type
        c["description"] = description
        c["status"] = new_status
        c["next_contact_date"] = next_contact
        c["last_comment"] = comment

        self.contact_comment.clear()
        QMessageBox.information(self, "Success",
            f"Data saved.\nStatus changed to '{new_status}'.\nContact recorded.")

        if self.search_input.text().strip():
            self._perform_search()
        self._build_client_card_view()

    # ═══════════════════════════════════════════════════════════════════
    #  ДОБАВЛЕНИЕ КОНТРАГЕНТА
    # ═══════════════════════════════════════════════════════════════════

    def _add_counterparty_dialog(self):
        from ui.add_counterparty import AddCounterpartyDialog
        dialog = AddCounterpartyDialog(self.crm, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            if self.search_input.text().strip():
                self._perform_search()

    # ═══════════════════════════════════════════════════════════════════
    #  ПУБЛИЧНЫЕ МЕТОДЫ
    # ═══════════════════════════════════════════════════════════════════

    def show_filtered(self, client_ids):
        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        all_clients = self.crm.get_all_counterparties()
        self.search_results = [c for c in all_clients if c["id"] in client_ids]
        self._populate_results_table(self.search_results)
        self.selected_client = None
        self._show_placeholder()