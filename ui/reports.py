"""
InterTrade CRM — отчёты
"""

import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QPushButton, QDateEdit, QSpinBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import pandas as pd


class ReportsTab(QWidget):
    """Отчёты — показатели и экспорт"""

    def __init__(self, crm, switch_to_workspace=None):
        super().__init__()
        self.crm = crm
        self.switch_to_workspace = switch_to_workspace
        self.current_start = None
        self.current_end = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Фильтр периода
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            "background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;"
        )
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(10)

        fl.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Day", "Week", "Month", "Quarter", "Year", "Custom"])
        self.period_combo.setStyleSheet(
            "padding: 8px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px; min-width: 120px;"
        )
        self.period_combo.currentTextChanged.connect(self._on_period_changed)
        fl.addWidget(self.period_combo)

        self.period_stack = QWidget()
        self.period_stack_layout = QHBoxLayout(self.period_stack)
        self.period_stack_layout.setContentsMargins(0, 0, 0, 0)
        self.period_stack_layout.setSpacing(10)
        fl.addWidget(self.period_stack, stretch=1)
        fl.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(
            "background-color: #2563EB; color: white; padding: 10px 20px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"
        )
        refresh_btn.clicked.connect(self._refresh)
        fl.addWidget(refresh_btn)

        layout.addWidget(filter_frame)

        self.period_combo.setCurrentText("Month")
        self._on_period_changed("Month")
        self.current_start, self.current_end = self._get_period_dates()

        # Основная область
        main_area = QHBoxLayout()
        main_area.setSpacing(12)

        # Левая панель — выгрузка
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px;")
        left_panel.setFixedWidth(200)
        ll = QVBoxLayout(left_panel)
        ll.setContentsMargins(14, 14, 14, 14)
        ll.setSpacing(12)

        ll.addWidget(QLabel("Export Reports"))
        excel_btn = QPushButton("Export Excel")
        excel_btn.setStyleSheet(
            "background-color: #10B981; color: white; padding: 10px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"
        )
        excel_btn.clicked.connect(self._export_excel)
        ll.addWidget(excel_btn)

        self.update_time = QLabel("")
        self.update_time.setFont(QFont("Arial", 9))
        self.update_time.setStyleSheet("color: #94A3B8;")
        self.update_time.setWordWrap(True)
        ll.addWidget(self.update_time)
        ll.addStretch()
        main_area.addWidget(left_panel)

        # Правая панель — показатели
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_layout.setSpacing(12)
        right_panel.setWidget(self.stats_widget)
        main_area.addWidget(right_panel, stretch=1)

        layout.addLayout(main_area, stretch=1)

    def _on_period_changed(self, period):
        while self.period_stack_layout.count():
            item = self.period_stack_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        ins = "padding: 8px; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px;"

        if period == "Day":
            self.date_from = QDateEdit()
            self.date_from.setCalendarPopup(True)
            self.date_from.setDate(QDate.currentDate())
            self.date_from.setStyleSheet(ins)
            self.period_stack_layout.addWidget(QLabel("Date:"))
            self.period_stack_layout.addWidget(self.date_from)

        elif period == "Week":
            self.week_spin = QSpinBox()
            self.week_spin.setRange(1, 53)
            self.week_spin.setValue(QDate.currentDate().weekNumber()[0])
            self.week_spin.setStyleSheet(ins)
            self.year_spin_week = QSpinBox()
            self.year_spin_week.setRange(2020, 2100)
            self.year_spin_week.setValue(QDate.currentDate().year())
            self.year_spin_week.setStyleSheet(ins)
            self.period_stack_layout.addWidget(QLabel("Week #"))
            self.period_stack_layout.addWidget(self.week_spin)
            self.period_stack_layout.addWidget(QLabel("Year"))
            self.period_stack_layout.addWidget(self.year_spin_week)

        elif period == "Month":
            self.month_combo = QComboBox()
            self.month_combo.addItems(["January", "February", "March", "April", "May", "June",
                                        "July", "August", "September", "October", "November", "December"])
            self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)
            self.month_combo.setStyleSheet(ins)
            self.year_spin_month = QSpinBox()
            self.year_spin_month.setRange(2020, 2100)
            self.year_spin_month.setValue(QDate.currentDate().year())
            self.year_spin_month.setStyleSheet(ins)
            self.period_stack_layout.addWidget(self.month_combo)
            self.period_stack_layout.addWidget(self.year_spin_month)

        elif period == "Quarter":
            self.quarter_combo = QComboBox()
            self.quarter_combo.addItems(["Q1", "Q2", "Q3", "Q4"])
            self.quarter_combo.setCurrentIndex((QDate.currentDate().month() - 1) // 3)
            self.quarter_combo.setStyleSheet(ins)
            self.year_spin_quarter = QSpinBox()
            self.year_spin_quarter.setRange(2020, 2100)
            self.year_spin_quarter.setValue(QDate.currentDate().year())
            self.year_spin_quarter.setStyleSheet(ins)
            self.period_stack_layout.addWidget(self.quarter_combo)
            self.period_stack_layout.addWidget(self.year_spin_quarter)

        elif period == "Year":
            self.year_spin = QSpinBox()
            self.year_spin.setRange(2020, 2100)
            self.year_spin.setValue(QDate.currentDate().year())
            self.year_spin.setStyleSheet(ins)
            self.period_stack_layout.addWidget(QLabel("Year"))
            self.period_stack_layout.addWidget(self.year_spin)

        elif period == "Custom":
            self.date_from = QDateEdit()
            self.date_from.setCalendarPopup(True)
            self.date_from.setDate(QDate.currentDate().addMonths(-1))
            self.date_from.setStyleSheet(ins)
            self.date_to = QDateEdit()
            self.date_to.setCalendarPopup(True)
            self.date_to.setDate(QDate.currentDate())
            self.date_to.setStyleSheet(ins)
            self.period_stack_layout.addWidget(QLabel("From:"))
            self.period_stack_layout.addWidget(self.date_from)
            self.period_stack_layout.addWidget(QLabel("To:"))
            self.period_stack_layout.addWidget(self.date_to)

    def _get_period_dates(self):
        period = self.period_combo.currentText()
        if period == "Day":
            d = self.date_from.date().toPyDate()
            return d.strftime("%Y-%m-%d"), d.strftime("%Y-%m-%d")
        elif period == "Week":
            week = self.week_spin.value()
            year = self.year_spin_week.value()
            jan4 = datetime(year, 1, 4)
            start = jan4 - timedelta(days=jan4.weekday()) + timedelta(weeks=week - 1)
            end = start + timedelta(days=6)
        elif period == "Month":
            month = self.month_combo.currentIndex() + 1
            year = self.year_spin_month.value()
            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(year, month + 1, 1) - timedelta(days=1)
        elif period == "Quarter":
            q = self.quarter_combo.currentIndex() + 1
            year = self.year_spin_quarter.value()
            start = datetime(year, (q - 1) * 3 + 1, 1)
            end_month = (q - 1) * 3 + 3
            if end_month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(year, end_month + 1, 1) - timedelta(days=1)
        elif period == "Year":
            year = self.year_spin.value()
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)
        elif period == "Custom":
            start = self.date_from.date().toPyDate()
            end = self.date_to.date().toPyDate()
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def _refresh(self):
        self.current_start, self.current_end = self._get_period_dates()
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stats = self._get_stats()

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        row1.addWidget(self._tile("Total Contacts", str(stats["total_contacts"]), "#DBEAFE", "#2563EB"))
        row1.addWidget(self._tile("New Leads", str(stats["new_leads"]), "#FEE2E2", "#EF4444", "New"))
        row1.addWidget(self._tile("To Negotiation", str(stats["to_negotiation"]), "#FEF3C7", "#D97706", "Negotiation"))
        self.stats_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        row2.addWidget(self._tile("Deals Closed", str(stats["to_closed"]), "#D1FAE5", "#059669", "Deal Closed"))
        row2.addWidget(self._tile("Lost / Blocked", str(stats["lost"]), "#F1F5F9", "#6B7280", "lost"))
        row2.addWidget(self._tile("Overdue SLA", str(stats["overdue"]), "#FEE2E2", "#DC2626", "overdue"))
        self.stats_layout.addLayout(row2)

        # Последние контакты
        self.stats_layout.addWidget(QLabel("Recent Contacts"))
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Client", "Status Change", "Comment"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.setMaximumHeight(150)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; border: 1px solid #E2E8F0; }
            QHeaderView::section { background-color: #F1F5F9; color: #475569; font-weight: bold; padding: 6px; }
        """)
        recent = self._get_recent_contacts(5)
        table.setRowCount(len(recent))
        for i, r in enumerate(recent):
            table.setItem(i, 0, QTableWidgetItem(r["date"]))
            table.setItem(i, 1, QTableWidgetItem(r["name"]))
            table.setItem(i, 2, QTableWidgetItem(f"{r['old_status']} -> {r['new_status']}"))
            table.setItem(i, 3, QTableWidgetItem(r["comment"][:50]))
        self.stats_layout.addWidget(table)

        self.update_time.setText(f"Data as of:\n{datetime.now().strftime('%d.%m.%Y %H:%M')}")
        self.stats_layout.addStretch()

    def _tile(self, title, value, bg, fg, filter_key=None):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {bg}; border-radius: 10px; border: 1px solid #E2E8F0;")
        frame.setMinimumHeight(70)
        if filter_key:
            frame.setCursor(Qt.CursorShape.PointingHandCursor)
            frame.mousePressEvent = lambda e, k=filter_key: self._on_tile_click(k)
        l = QVBoxLayout(frame)
        l.setContentsMargins(14, 10, 14, 10)
        l.setSpacing(4)
        t = QLabel(title)
        t.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        t.setStyleSheet(f"color: {fg};")
        v = QLabel(str(value))
        v.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        v.setStyleSheet(f"color: {fg};")
        l.addWidget(t)
        l.addWidget(v)
        return frame

    def _on_tile_click(self, filter_key):
        if not self.switch_to_workspace:
            return
        if filter_key == "overdue":
            ids = self._get_overdue_ids()
        elif filter_key == "lost":
            ids = self._get_lost_ids()
        else:
            ids = [c["id"] for c in self.crm.get_all_counterparties() if c["status"] == filter_key]
        if ids:
            self.switch_to_workspace(ids)
        else:
            QMessageBox.information(self, "No Data", "No counterparties match this filter.")

    def _get_stats(self):
        start, end = self.current_start, self.current_end
        self.crm.cursor.execute("SELECT COUNT(*) FROM status_history WHERE changed_at BETWEEN ? AND ?", (start, end))
        total_contacts = self.crm.cursor.fetchone()[0]

        self.crm.cursor.execute("SELECT COUNT(*) FROM status_history WHERE status_name = 'New' AND changed_at BETWEEN ? AND ?", (start, end))
        new_leads = self.crm.cursor.fetchone()[0]

        self.crm.cursor.execute("SELECT COUNT(*) FROM status_history WHERE status_name = 'Negotiation' AND changed_at BETWEEN ? AND ?", (start, end))
        to_negotiation = self.crm.cursor.fetchone()[0]

        self.crm.cursor.execute("SELECT COUNT(*) FROM status_history WHERE status_name = 'Deal Closed' AND changed_at BETWEEN ? AND ?", (start, end))
        to_closed = self.crm.cursor.fetchone()[0]

        self.crm.cursor.execute("SELECT COUNT(*) FROM status_history WHERE status_name IN ('Blocked', 'Refusal') AND changed_at BETWEEN ? AND ?", (start, end))
        lost = self.crm.cursor.fetchone()[0]

        overdue = len(self._get_overdue_ids())

        return {
            "total_contacts": total_contacts,
            "new_leads": new_leads,
            "to_negotiation": to_negotiation,
            "to_closed": to_closed,
            "lost": lost,
            "overdue": overdue,
        }

    def _get_overdue_ids(self):
        sla_config = self.crm.get_sla_config()
        clients = self.crm.get_all_counterparties()
        current_date = datetime.now()
        self.crm.cursor.execute("SELECT counterparty_id, MAX(changed_at) FROM status_history GROUP BY counterparty_id")
        last_changes = {row[0]: row[1] for row in self.crm.cursor.fetchall()}
        ids = []
        for c in clients:
            status = c["status"]
            if status in sla_config["alerts"] and status != "New":
                limit = sla_config["alerts"][status]["days"]
                if limit == 0:
                    continue
                last = last_changes.get(c["id"])
                if last:
                    try:
                        days = (current_date - datetime.strptime(last.split(" ")[0], "%Y-%m-%d")).days
                        if days > limit:
                            ids.append(c["id"])
                    except Exception:
                        pass
        return ids

    def _get_lost_ids(self):
        return [c["id"] for c in self.crm.get_all_counterparties() if c["status"] in ("Blocked", "Refusal", "Sleeping")]

    def _get_recent_contacts(self, limit=5):
        self.crm.cursor.execute("""
            SELECT sh.changed_at, cp.name, sh.status_name,
                   (SELECT sh2.status_name FROM status_history sh2
                    WHERE sh2.counterparty_id = sh.counterparty_id AND sh2.changed_at < sh.changed_at
                    ORDER BY sh2.changed_at DESC LIMIT 1) as old_status,
                   cp.last_comment
            FROM status_history sh
            JOIN counterparties cp ON sh.counterparty_id = cp.id
            ORDER BY sh.changed_at DESC, sh.id DESC LIMIT ?
        """, (limit,))
        result = []
        for row in self.crm.cursor.fetchall():
            result.append({
                "date": row[0],
                "name": self.crm._decrypt_val(row[1]) if row[1] else "?",
                "old_status": row[3] if row[3] else "New",
                "new_status": row[2],
                "comment": self.crm._decrypt_val(row[4]) if row[4] else "",
            })
        return result

    def _export_excel(self):
        if not self.current_start or not self.current_end:
            QMessageBox.warning(self, "Error", "Click 'Refresh' before export.")
            return

        stats = self._get_stats()
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filename = f"Report_{self.current_start}_{self.current_end}.xlsx"
        filepath = os.path.join(desktop, filename)

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            summary = pd.DataFrame([
                ["Total Contacts", stats["total_contacts"]],
                ["New Leads", stats["new_leads"]],
                ["To Negotiation", stats["to_negotiation"]],
                ["Deals Closed", stats["to_closed"]],
                ["Lost / Blocked", stats["lost"]],
                ["Overdue SLA", stats["overdue"]],
            ], columns=["Metric", "Value"])
            summary.to_excel(writer, sheet_name="Summary", index=False)

            status_data = []
            for status in self.crm.get_statuses():
                count = sum(1 for c in self.crm.get_all_counterparties() if c["status"] == status)
                status_data.append({"Status": status, "Count": count})
            pd.DataFrame(status_data).to_excel(writer, sheet_name="By Status", index=False)

        QMessageBox.information(self, "Done", f"Report saved to Desktop:\n{filename}")