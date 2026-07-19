"""
InterTrade CRM — дашборд
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime


class DashboardTab(QWidget):
    """Дашборд — плитки SLA + сводка"""

    def __init__(self, crm, switch_to_workspace=None):
        super().__init__()
        self.crm = crm
        self.switch_to_workspace = switch_to_workspace
        self._build_ui()

    def _build_ui(self):
        if self.layout():
            QWidget().setLayout(self.layout())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setSpacing(16)

        stats = self._get_dashboard_stats()

        # Плитки SLA (3 колонки)
        grid = QGridLayout()
        grid.setSpacing(12)

        sla_tiles = [t for t in stats["tiles"] if t["key"] != "total"]
        for idx, tile_data in enumerate(sla_tiles):
            tile = self._create_tile(
                tile_data["count"], tile_data["title"], tile_data["hint"],
                tile_data["color"], tile_data["text_color"],
            )
            tile.setCursor(Qt.CursorShape.PointingHandCursor)
            tile.mousePressEvent = lambda event, k=tile_data["key"]: self._on_tile_click(k)
            grid.addWidget(tile, idx // 3, idx % 3)

        sl.addLayout(grid)

        # Плитка «Всего»
        total_data = next((t for t in stats["tiles"] if t["key"] == "total"), None)
        if total_data:
            tf = QFrame()
            tf.setStyleSheet(
                f"background-color: {total_data['color']}; border-radius: 12px; border: 1px solid #E2E8F0;"
            )
            tf.setToolTip(total_data["hint"])
            tf.setFixedHeight(80)
            tl = QHBoxLayout(tf)
            tl.setContentsMargins(24, 12, 24, 12)
            tt = QLabel(total_data["title"])
            tt.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            tt.setStyleSheet(f"color: {total_data['text_color']};")
            tc = QLabel(str(total_data["count"]))
            tc.setFont(QFont("Arial", 28, QFont.Weight.Bold))
            tc.setStyleSheet(f"color: {total_data['text_color']};")
            tc.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tl.addWidget(tt)
            tl.addStretch()
            tl.addWidget(tc)
            sl.addWidget(tf)

        # Сводка
        info = QFrame()
        info.setStyleSheet("background-color: #F8FAFC; border-radius: 10px; border: 1px solid #E2E8F0;")
        il = QVBoxLayout(info)
        il.setContentsMargins(20, 16, 20, 16)
        active = sum(1 for t in sla_tiles if t['count'] > 0)
        txt = (f"OPERATIONAL SUMMARY:\n\n"
               f"Total sales volume: {stats['total_sales']:,.2f} {self.crm.get_base_currency()}\n"
               f"Total counterparties: {stats['total']}\n"
               f"Statuses requiring attention: {active} of {len(sla_tiles)}")
        it = QLabel(txt)
        it.setFont(QFont("Arial", 11, QFont.Weight.Medium))
        it.setStyleSheet("color: #475569; line-height: 160%;")
        it.setWordWrap(True)
        il.addWidget(it)
        sl.addWidget(info)
        sl.addStretch()

        scroll.setWidget(sw)
        outer.addWidget(scroll)

    def _create_tile(self, count, title, hint, bg_color, text_color):
        if count == 0:
            bg_color = "#F1F5F9"
            text_color = "#94A3B8"

        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {bg_color}; border-radius: 12px; border: 1px solid #E2E8F0;"
        )
        frame.setToolTip(hint)
        frame.setMinimumHeight(135)
        frame.setMaximumHeight(150)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 10)
        layout.setSpacing(4)

        t = QLabel(title)
        t.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        t.setStyleSheet(f"color: {text_color};")
        t.setWordWrap(True)
        t.setFixedHeight(32)

        v = QLabel(str(count))
        v.setFont(QFont("Arial", 30, QFont.Weight.Bold))
        v.setStyleSheet(f"color: {text_color};")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h = QLabel(hint)
        h.setFont(QFont("Arial", 7))
        h.setStyleSheet(f"color: {text_color}; opacity: 0.65;")
        h.setWordWrap(True)
        h.setFixedHeight(26)

        layout.addWidget(t)
        layout.addWidget(v)
        layout.addWidget(h)
        return frame

    def _on_tile_click(self, filter_key):
        problem_ids = self._get_clients_by_filter(filter_key)
        if not problem_ids:
            QMessageBox.information(self, "No Data", "No counterparties match this filter.")
            return
        if self.switch_to_workspace:
            self.switch_to_workspace(problem_ids)

    def _get_dashboard_stats(self):
        clients = self.crm.get_all_counterparties()
        sla_config = self.crm.get_sla_config()
        current_date = datetime.now()
        total_count = len(clients)

        tile_defs = {
            "alert_New": {"count": 0, "title": "New", "hint": "All new leads require immediate contact.",
                          "color": "#FEE2E2", "text_color": "#EF4444"},
            "alert_Verification": {"count": 0, "title": "Verification > 3d", "hint": "Qualification overdue.",
                                   "color": "#FEF3C7", "text_color": "#D97706"},
            "alert_Negotiation": {"count": 0, "title": "Negotiation > 7d", "hint": "Negotiations stalled.",
                                  "color": "#FEF3C7", "text_color": "#D97706"},
            "alert_Proposal": {"count": 0, "title": "Proposal > 5d", "hint": "Proposal without response.",
                               "color": "#DBEAFE", "text_color": "#2563EB"},
            "alert_Awaiting Payment": {"count": 0, "title": "Awaiting Payment > 3d", "hint": "Payment overdue.",
                                        "color": "#FEE2E2", "text_color": "#DC2626"},
            "alert_Paid": {"count": 0, "title": "Paid > 14d", "hint": "Shipment control overdue.",
                           "color": "#DBEAFE", "text_color": "#2563EB"},
            "alert_Deal Closed": {"count": 0, "title": "Deal Closed > 7d", "hint": "Feedback needed.",
                                  "color": "#D1FAE5", "text_color": "#059669"},
            "alert_Regular": {"count": 0, "title": "Regular > 30d", "hint": "Scheduled contact overdue.",
                              "color": "#D1FAE5", "text_color": "#059669"},
            "alert_Rare": {"count": 0, "title": "Rare > 45d", "hint": "Reactivation needed.",
                           "color": "#FEF3C7", "text_color": "#92400E"},
            "alert_On Hold": {"count": 0, "title": "On Hold > 60d", "hint": "Check status.",
                              "color": "#E0E7FF", "text_color": "#4338CA"},
            "alert_Contact by Date": {"count": 0, "title": "Contact by Date", "hint": "Contact date reached.",
                                       "color": "#FEE2E2", "text_color": "#DC2626"},
            "reanimation": {"count": 0, "title": "Sleeping > 90d", "hint": "No sales > 90 days. Reanimate.",
                            "color": "#F1F5F9", "text_color": "#6B7280"},
            "total": {"count": total_count, "title": "Total Counterparties",
                      "hint": "Total cards in database.",
                      "color": "#DBEAFE", "text_color": "#2563EB"},
        }

        self.crm.cursor.execute(
            "SELECT counterparty_id, MAX(changed_at) FROM status_history GROUP BY counterparty_id"
        )
        last_changes = {row[0]: row[1] for row in self.crm.cursor.fetchall()}

        for client in clients:
            status = client["status"]
            cid = client["id"]

            if status == "New":
                tile_defs["alert_New"]["count"] += 1
                continue

            if status == "Contact by Date":
                nd = client.get("next_contact_date", "")
                if nd:
                    try:
                        nd_clean = nd.split(" ")[0]
                        if current_date >= datetime.strptime(nd_clean, "%Y-%m-%d"):
                            tile_defs["alert_Contact by Date"]["count"] += 1
                    except (ValueError, TypeError):
                        tile_defs["alert_Contact by Date"]["count"] += 1
                else:
                    tile_defs["alert_Contact by Date"]["count"] += 1
                continue

            key = f"alert_{status}"
            if key in tile_defs:
                limit = sla_config["alerts"].get(status, {}).get("days", 0)
                if limit == 0:
                    continue
                last_change = last_changes.get(cid)
                days_in_status = 0
                if last_change:
                    try:
                        days_in_status = (current_date - datetime.strptime(
                            last_change.split(" ")[0], "%Y-%m-%d")).days
                    except (ValueError, TypeError):
                        pass
                elif client.get("created_at"):
                    try:
                        days_in_status = (current_date - datetime.strptime(
                            client["created_at"].split(" ")[0], "%Y-%m-%d")).days
                    except (ValueError, TypeError):
                        pass
                if days_in_status > limit:
                    tile_defs[key]["count"] += 1

            # Реанимация Sleeping
            if status == "Sleeping":
                if (client["sales_amount"] or 0) > 0 and client["last_sale_date"]:
                    try:
                        sale_date = datetime.strptime(client["last_sale_date"], "%d.%m.%Y")
                        if (current_date - sale_date).days > sla_config["reanimation"]["days"]:
                            tile_defs["reanimation"]["count"] += 1
                    except (ValueError, TypeError):
                        pass

        tiles = []
        for k, v in tile_defs.items():
            v["key"] = k
            tiles.append(v)

        return {
            "tiles": tiles,
            "total": total_count,
            "total_sales": sum(c["sales_amount"] or 0.0 for c in clients),
        }

    def _get_clients_by_filter(self, filter_key):
        clients = self.crm.get_all_counterparties()
        sla_config = self.crm.get_sla_config()
        current_date = datetime.now()

        self.crm.cursor.execute(
            "SELECT counterparty_id, MAX(changed_at) FROM status_history GROUP BY counterparty_id"
        )
        last_changes = {row[0]: row[1] for row in self.crm.cursor.fetchall()}

        result_ids = []

        for c in clients:
            if filter_key == "alert_New" and c["status"] == "New":
                result_ids.append(c["id"])
            elif filter_key == "reanimation":
                if c["status"] == "Sleeping" and c["last_sale_date"]:
                    try:
                        sale_date = datetime.strptime(c["last_sale_date"], "%d.%m.%Y")
                        if (current_date - sale_date).days > sla_config["reanimation"]["days"]:
                            result_ids.append(c["id"])
                    except (ValueError, TypeError):
                        pass
            elif filter_key == "alert_Contact by Date" and c["status"] == "Contact by Date":
                nd = c.get("next_contact_date", "")
                if nd:
                    try:
                        nd_clean = nd.split(" ")[0]
                        if current_date >= datetime.strptime(nd_clean, "%Y-%m-%d"):
                            result_ids.append(c["id"])
                    except (ValueError, TypeError):
                        result_ids.append(c["id"])
                else:
                    result_ids.append(c["id"])
            elif filter_key.startswith("alert_"):
                status_name = filter_key.replace("alert_", "")
                if c["status"] == status_name:
                    limit = sla_config["alerts"].get(status_name, {}).get("days", 0)
                    if limit == 0:
                        continue
                    last_change = last_changes.get(c["id"])
                    days_in_status = 0
                    if last_change:
                        try:
                            days_in_status = (current_date - datetime.strptime(
                                last_change.split(" ")[0], "%Y-%m-%d")).days
                        except (ValueError, TypeError):
                            pass
                    if days_in_status > limit:
                        result_ids.append(c["id"])

        return result_ids

    def refresh(self):
        if self.layout():
            QWidget().setLayout(self.layout())
        self._build_ui()