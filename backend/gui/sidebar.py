from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)

from PySide6.QtCore import (
    Signal,
    QPropertyAnimation,
    QEasingCurve,
    QEvent,
)


class Sidebar(QWidget):

    dashboard_clicked = Signal()
    documents_clicked = Signal()
    clients_clicked = Signal()
    search_clicked = Signal()
    backup_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("sidebar")
        self.expanded_width = 240
        self.collapsed_width = 75

        self.setFixedWidth(self.collapsed_width)
        self.animation = None

        self.setMouseTracking(True)
        self.installEventFilter(self)

        self.create_interface()

    def create_interface(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(14)
        self.setLayout(layout)

        self.title = QLabel("💻")
        self.title.setObjectName("sidebar_title")

        layout.addWidget(self.title)

        self.dashboard_btn = self.create_button("📍", "Dashboard")
        self.documents_btn = self.create_button("📑", "Documents")
        self.clients_btn = self.create_button("👥", "Clients")
        self.search_btn = self.create_button("🔍", "Search NIP")
        self.backup_btn = self.create_button("💾", "Backup")
        self.settings_btn = self.create_button("⚙️", "Settings")

        buttons = [
            self.dashboard_btn,
            self.documents_btn,
            self.clients_btn,
            self.search_btn,
        ]

        for button in buttons:
            layout.addWidget(button)

        layout.addStretch()

        layout.addWidget(self.backup_btn)
        layout.addWidget(self.settings_btn)

        self.dashboard_btn.clicked.connect(self.dashboard_clicked.emit)
        self.documents_btn.clicked.connect(self.documents_clicked.emit)
        self.clients_btn.clicked.connect(self.clients_clicked.emit)
        self.search_btn.clicked.connect(self.search_clicked.emit)
        self.backup_btn.clicked.connect(self.backup_clicked.emit)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)

        self.hide_text()

    def create_button(self, icon, text):
        button = QPushButton(icon)
        button.setObjectName("sidebar_button")
        button.icon_text = icon
        button.full_text = text
        button.setFixedHeight(55)

        return button

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.Enter:
                self.expand_sidebar()
            elif event.type() == QEvent.Leave:
                self.collapse_sidebar()

        return super().eventFilter(obj, event)

    def animate_width(self, start, end):
        if self.animation:
            self.animation.stop()

        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(220)
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()

    def expand_sidebar(self):
        if self.width() >= self.expanded_width:
            return

        self.show_text()
        self.animate_width(self.width(), self.expanded_width)

    def collapse_sidebar(self):
        if self.width() <= self.collapsed_width:
            self.hide_text()
            return

        if self.animation:
            self.animation.stop()

        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(220)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(self.collapsed_width)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.finished.connect(self.hide_text)
        self.animation.start()

    def show_text(self):
        self.title.setText("💻 DocAuthorize")

        buttons = [
            self.dashboard_btn,
            self.documents_btn,
            self.clients_btn,
            self.search_btn,
            self.backup_btn,
            self.settings_btn,
        ]

        for btn in buttons:
            btn.setText(f"{btn.icon_text}   {btn.full_text}")
            btn.setProperty("expanded", "true")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def hide_text(self):
        self.title.setText("💻")

        buttons = [
            self.dashboard_btn,
            self.documents_btn,
            self.clients_btn,
            self.search_btn,
            self.backup_btn,
            self.settings_btn,
        ]

        for btn in buttons:
            btn.setText(btn.icon_text)
            btn.setProperty("expanded", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_language(self, lang):
        self.dashboard_btn.full_text = lang.get("dashboard", "Dashboard")
        self.documents_btn.full_text = lang.get("documents", "Documents")
        self.clients_btn.full_text = lang.get("clients", "Clients")
        self.search_btn.full_text = lang.get("search", "Search NIP")
        self.backup_btn.full_text = lang.get("backup", "Backup")
        self.settings_btn.full_text = lang.get("settings", "Settings")

        if self.width() > 100:
            self.show_text()


            #.