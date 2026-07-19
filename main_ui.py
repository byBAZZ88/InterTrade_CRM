"""
InterTrade CRM — главное окно
Версия: 1.0.0
"""

import sys
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QSplashScreen,
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QIcon, QPixmap
from core import CRMCore
from ui.login import LoginDialog
from ui.first_run import FirstRunDialog
from ui.dashboard import DashboardTab
from ui.workspace import WorkspaceTab
from ui.add_counterparty import AddCounterpartyDialog
from ui.import_data import ImportDataTab
from ui.settings import SettingsTab
from ui.reports import ReportsTab


def resource_path(relative_path):
    """Получить путь к ресурсу (работает и в EXE, и при запуске из исходников)."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("InterTrade CRM")
        self.resize(1280, 820)

        # Иконка приложения
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.crm = CRMCore()

        if self.crm.is_first_run():
            dialog = FirstRunDialog(self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                self.crm.setup_system(
                    dialog.organization_name,
                    dialog.admin_password,
                    dialog.base_currency,
                )
            else:
                QMessageBox.critical(self, "Error", "Setup incomplete. Application will close.")
                sys.exit(1)

        login = LoginDialog(self.crm, self)
        if login.exec() != login.DialogCode.Accepted:
            sys.exit(0)

        self._build_ui()

    def _build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 10)

        self._build_header(main_layout)
        self._build_tabs(main_layout)
        self._build_footer(main_layout)

        locked, lock_msg = self.crm.is_settings_locked()
        if locked:
            self.tabs.setTabEnabled(3, False)
            QTimer.singleShot(500, lambda: QMessageBox.warning(
                self, "Settings Locked", lock_msg
            ))

    def _build_header(self, parent):
        h = QHBoxLayout()

        # Логотип
        logo_path = resource_path("logo_header.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_label.setPixmap(QPixmap(logo_path))
            logo_label.setMaximumSize(100, 55)
            logo_label.setStyleSheet("margin-right: 12px;")
            h.addWidget(logo_label)

        title = QLabel("InterTrade CRM")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1E293B;")
        h.addWidget(title)

        h.addStretch()

        org = self.crm.get_organization_name()
        self.org_label = QLabel(f"Organization: {org}")
        self.org_label.setFont(QFont("Arial", 11, QFont.Weight.Medium))
        self.org_label.setStyleSheet(
            "background-color: #2563EB; color: white; padding: 6px 12px; border-radius: 6px;"
        )

        self.user_label = QLabel(f"User: {self.crm.current_user} ({self.crm.current_role})")
        self.user_label.setFont(QFont("Arial", 10))
        self.user_label.setStyleSheet("color: #64748B; padding: 4px 8px;")

        h.addWidget(self.user_label)
        h.addWidget(self.org_label)
        parent.addLayout(h)

    def _build_tabs(self, parent):
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::panel {
                border: 1px solid #CBD5E1; border-radius: 8px; background-color: #FFFFFF;
            }
            QTabBar::tab {
                background: #E2E8F0; color: #475569; padding: 10px 20px;
                font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF; color: #2563EB;
                border: 1px solid #CBD5E1; border-bottom-color: #FFFFFF;
            }
        """)

        self.dashboard_tab = DashboardTab(self.crm, switch_to_workspace=self._switch_to_workspace_filter)
        self.workspace_tab = WorkspaceTab(self.crm)
        self.import_tab = ImportDataTab(self.crm)
        self.tab_reports = ReportsTab(self.crm, switch_to_workspace=self._switch_to_workspace_filter)

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.workspace_tab, "Workspace")
        self.tabs.addTab(self.import_tab, "Import Data")
        self.tabs.addTab(self.tab_reports, "Reports")

        if self.crm.current_role in ("admin", "supervisor"):
            self.settings_tab = SettingsTab(self.crm)
            self.tabs.addTab(self.settings_tab, "Settings")

        parent.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _build_footer(self, parent):
        f = QHBoxLayout()

        dev_link = QLabel("<a href='https://bybazz88.github.io/' style='color: #64748B; text-decoration: none;'>byBAZZ</a>")
        dev_link.setFont(QFont("Arial", 9))
        dev_link.setOpenExternalLinks(True)

        copy = QLabel("InterTrade CRM v1.0.0 | 2026")
        copy.setFont(QFont("Arial", 9))
        copy.setStyleSheet("color: #94A3B8;")

        donate = QLabel("<a href='https://bybazz88.github.io/#support' style='color: #F59E0B; text-decoration: none;'>Donate</a>")
        donate.setFont(QFont("Arial", 9))
        donate.setOpenExternalLinks(True)

        f.addWidget(dev_link)
        f.addSpacing(8)
        f.addWidget(copy)
        f.addStretch()
        f.addWidget(donate)
        parent.addLayout(f)

    def _switch_to_workspace_filter(self, problem_ids):
        self.tabs.setCurrentIndex(1)
        self.workspace_tab.show_filtered(problem_ids)

    def _on_tab_changed(self, index):
        if index == 0:
            self.dashboard_tab.refresh()


def show_splash():
    """Показывает сплеш-скрин с эффектом появления."""
    splash_path = resource_path("logo_splash.png")
    if not os.path.exists(splash_path):
        return None, None

    pixmap = QPixmap(splash_path)
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
    splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    splash.setStyleSheet("background: transparent;")

    # Начальная прозрачность
    splash.setWindowOpacity(0.0)
    splash.show()

    # Анимация появления
    animation = QPropertyAnimation(splash, b"windowOpacity")
    animation.setDuration(600)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    animation.start()

    return splash, animation


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Установка иконки приложения
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    splash, anim = show_splash()

    # Показываем сплеш 1.8 секунды, затем открываем главное окно
    def launch():
        if splash:
            splash.close()
        window = MainWindow()
        window.show()

    QTimer.singleShot(1800, launch)
    sys.exit(app.exec())