from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout
)


class StatCard(QFrame):

    def __init__(self, title, value, icon):
        super().__init__()

        self.setFixedSize(220, 120)

        layout = QVBoxLayout()


        icon_label = QLabel(icon)

        title_label = QLabel(title)

        value_label = QLabel(value)


        layout.addWidget(icon_label)

        layout.addWidget(title_label)

        layout.addWidget(value_label)


        self.setLayout(layout)


        self.setStyleSheet("""
        
        QFrame {

            background-color: #1F2937;
            border-radius: 12px;

        }


        QLabel {

            color: white;

        }

        """)


        #.