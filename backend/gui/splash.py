from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect


class SplashScreen(QWidget):
    def __init__(self, on_finish_callback):
        super().__init__()
        self.on_finish_callback = on_finish_callback

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(550, 320)

        screen = self.screen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

        
        layout = QVBoxLayout(self)
        
        self.card = QWidget()
        self.card.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b);
                border-radius: 20px;
                border: 1px solid #334155;
            }
        """)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 30, 40, 25)

        self.title_label = QLabel("⚡ DocAuthorize")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #60a5fa;
            border: none;
        """)

        self.subtitle_label = QLabel("Contract & Document Authorization System")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            font-size: 13px;
            color: #94a3b8;
            border: none;
            margin-top: 6px;
        """)

        self.author_label = QLabel("Created by Mariia Ostrianska for PM Digital")
        self.author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.author_label.setStyleSheet("""
            font-size: 11px;
            font-style: italic;
            font-weight: 500;
            color: #38bdf8;
            border: none;
        """)

        card_layout.addStretch(1)
        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.subtitle_label)
        card_layout.addStretch(1)
        card_layout.addWidget(self.author_label)

        layout.addWidget(self.card)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.animate_fade_in()

    def animate_fade_in(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(1200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.anim.start()

        QTimer.singleShot(3500, self.finish_splash)

    def finish_splash(self):
        self.close()
        self.on_finish_callback()


        #.