from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
)
from PySide6.QtCore import QTimer, QSettings

from gui.pages.dashboard import Dashboard
from gui.pages.documents import Documents
from gui.pages.clients import Clients
from gui.pages.search import Search
from gui.pages.settings import Settings
from gui.sidebar import Sidebar
from translations.manager import LanguageManager
from services.backup import create_database_backup


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DocAuthorize")
        self.resize(1200, 700)

        self.lang = LanguageManager()
        self.create_interface()

        settings = QSettings("DocAuthorize", "ContractManager")
        saved_lang = settings.value("app_language", "ENG")
        self.change_language(saved_lang)

        self.backup_timer = QTimer(self)
        self.backup_timer.setInterval(30 * 60 * 1000)
        self.backup_timer.timeout.connect(self.auto_backup)
        self.backup_timer.start()

    def auto_backup(self):
        """Silent auto-backup every 30 minutes without user notification."""
        try:
            create_database_backup(backup_dir="backups")
            print("[AutoBackup] Automatic backup has been created successfully.")
        except Exception as e:
            print(f"[AutoBackup Error] {e}")

    def create_interface(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)

        top_bar = QHBoxLayout()
        top_bar.addStretch()

        self.eng_btn = QPushButton("ENG")
        self.pol_btn = QPushButton("POL")

        for btn in [self.eng_btn, self.pol_btn]:
            btn.setFixedSize(55, 32)
            btn.setStyleSheet("""
                QPushButton {
                    background-color:#1c2b40;
                    color:white;
                    border-radius:8px;
                    font-weight:bold;
                }
                QPushButton:hover {
                    background-color:#263b58;
                }
            """)

        top_bar.addWidget(self.eng_btn)
        top_bar.addWidget(self.pol_btn)

        content_layout.addLayout(top_bar)

        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages)

        self.dashboard_page = Dashboard()
        self.documents_page = Documents()
        self.clients_page = Clients()
        self.search_page = Search()
        self.settings_page = Settings()

        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.documents_page)
        self.pages.addWidget(self.clients_page)
        self.pages.addWidget(self.search_page)
        self.pages.addWidget(self.settings_page)

        main_layout.addWidget(content)

        self.sidebar.dashboard_clicked.connect(
            lambda: self.pages.setCurrentWidget(self.dashboard_page)
        )
        self.sidebar.documents_clicked.connect(
            lambda: self.pages.setCurrentWidget(self.documents_page)
        )
        self.sidebar.clients_clicked.connect(
            lambda: self.pages.setCurrentWidget(self.clients_page)
        )
        self.sidebar.search_clicked.connect(
            lambda: self.pages.setCurrentWidget(self.search_page)
        )
        
        if hasattr(self.sidebar, "settings_clicked"):
            self.sidebar.settings_clicked.connect(
                lambda: self.pages.setCurrentWidget(self.settings_page)
            )

        if hasattr(self.sidebar, "backup_clicked"):
            self.sidebar.backup_clicked.connect(self.make_manual_backup)

        self.eng_btn.clicked.connect(lambda: self.change_language("ENG"))
        self.pol_btn.clicked.connect(lambda: self.change_language("POL"))

    def make_manual_backup(self):
        """Manual backup with notification."""
        try:
            create_database_backup(backup_dir="backups")
            QMessageBox.information(
                self,
                "Backup Success",
                "✅ Database backup has been successfully created in the 'backups' folder!"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Backup Error",
                f"❌ Could not create backup: {e}"
            )

    def change_language(self, language):
        self.lang.set_language(language)
        
        settings = QSettings("DocAuthorize", "ContractManager")
        settings.setValue("app_language", language)

        self.update_language_buttons(language)

        self.sidebar.set_language(self.lang)
        self.dashboard_page.set_language(self.lang)
        self.documents_page.set_language(self.lang)
        self.clients_page.set_language(self.lang)
        self.search_page.set_language(self.lang)
        self.settings_page.set_language(self.lang)

    def update_language_buttons(self, language):
        active = """
        QPushButton {
            background-color:#2563eb;
            color:white;
            border-radius:8px;
            font-weight:bold;
        }
        """

        normal = """
        QPushButton {
            background-color:#1c2b40;
            color:white;
            border-radius:8px;
            font-weight:bold;
        }
        """

        if language == "ENG":
            self.eng_btn.setStyleSheet(active)
            self.pol_btn.setStyleSheet(normal)
        else:
            self.pol_btn.setStyleSheet(active)
            self.eng_btn.setStyleSheet(normal)


           #.