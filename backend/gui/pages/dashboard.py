from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QApplication,
)
from PySide6.QtCore import Qt, QSettings

from database.db import get_dashboard_stats
from gui.styles.dark_theme import DARK_THEME
from gui.styles.light_theme import LIGHT_THEME


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()
        self.settings = QSettings("DocAuthorize", "ContractManager")
        self.create_interface()

    def create_interface(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        header_layout = QHBoxLayout()

        title_container = QVBoxLayout()
        self.title = QLabel("📊 Dashboard")
        self.title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                border: none;
            }
        """)

        self.subtitle = QLabel("Document analysis overview")
        self.subtitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #94a3b8;
                border: none;
                margin-top: -4px;
            }
        """)
        title_container.addWidget(self.title)
        title_container.addWidget(self.subtitle)

        header_layout.addLayout(title_container)
        header_layout.addStretch()

        # Кнопка смены темы
        is_dark = self.settings.value("theme_is_dark", True, type=bool)
        btn_text = "☀️" if is_dark else "🌙"

        self.theme_button = QPushButton(btn_text)
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.theme_button.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_button)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(18)

        stats = get_dashboard_stats()

        self.documents_card = self.create_card(
            "📄", "Documents", stats.get("documents", 0), "#3b82f6"
        )
        self.clients_card = self.create_card(
            "👥", "Clients", stats.get("clients", 0), "#10b981"
        )

        stats_layout.addWidget(self.documents_card)
        stats_layout.addWidget(self.clients_card)

        main_layout.addLayout(stats_layout)
        main_layout.addSpacing(30)

        # Блок недавней активности
        activity = QFrame()
        activity.setStyleSheet("""
            QFrame {
                border-radius: 16px;
                border: 1px solid #334155;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        activity_layout = QVBoxLayout(activity)
        activity_layout.setContentsMargins(24, 22, 24, 22)
        activity_layout.setSpacing(12)

        self.activity_title = QLabel("📌 Recent activity")
        self.activity_title.setStyleSheet("""
            QLabel {
                font-size: 17px;
                font-weight: bold;
            }
        """)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #334155; border: none; height: 1px;")

        self.activity_text = QLabel(
            "<p style='line-height: 1.6; font-size: 14px; margin: 0;'>"
            "• New documents added<br>"
            "• Contract changes registered"
            "</p>"
        )

        activity_layout.addWidget(self.activity_title)
        activity_layout.addWidget(line)
        activity_layout.addWidget(self.activity_text)

        main_layout.addWidget(activity)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_card(self, icon, name, value, color):
        card = QFrame()
        card.setFixedHeight(120)
        card.setStyleSheet("""
            QFrame {
                border-radius: 16px;
                border: 1px solid #334155;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px; background: transparent; border: none;")

        name_label = QLabel(name)
        name_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        card.name_label = name_label

        top_row.addWidget(icon_label)
        top_row.addWidget(name_label)
        top_row.addStretch()

        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {color};
                font-size: 32px;
                font-weight: bold;
            }}
        """)
        card.value_label = value_label

        layout.addLayout(top_row)
        layout.addWidget(value_label)

        return card

    def showEvent(self, event):
        """Automatic update of statistics when you click on the Dashboard tab."""
        super().showEvent(event)
        self.refresh_stats()

    def refresh_stats(self):
        """Recalculation of statistics from the database."""
        stats = get_dashboard_stats()
        if hasattr(self, 'documents_card') and hasattr(self.documents_card, 'value_label'):
            self.documents_card.value_label.setText(str(stats.get("documents", 0)))
        if hasattr(self, 'clients_card') and hasattr(self.clients_card, 'value_label'):
            self.clients_card.value_label.setText(str(stats.get("clients", 0)))

    def toggle_theme(self):
        """Switch between Light and Dark themes."""
        is_dark = self.settings.value("theme_is_dark", True, type=bool)
        new_state = not is_dark
        self.settings.setValue("theme_is_dark", new_state)

        if new_state:
            QApplication.instance().setStyleSheet(DARK_THEME)
            self.theme_button.setText("☀️")
        else:
            QApplication.instance().setStyleSheet(LIGHT_THEME)
            self.theme_button.setText("🌙")

    def set_language(self, lang):
        self.title.setText("📊 " + lang.get("dashboard", "Dashboard"))
        self.subtitle.setText(lang.get("dashboard_subtitle", "Document analysis overview"))

        self.documents_card.name_label.setText(lang.get("documents", "Documents"))
        self.clients_card.name_label.setText(lang.get("clients", "Clients"))

        self.activity_title.setText("📌 " + lang.get("recent_activity", "Recent activity"))

        self.activity_text.setText(
            f"<p style='line-height: 1.6; font-size: 14px; margin: 0;'>"
            f"• {lang.get('new_documents', 'New documents added')}<br>"
            f"• {lang.get('contract_changes', 'Contract changes registered')}"
            f"</p>"
        )
        self.refresh_stats()

#.